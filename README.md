# Autoalerter (модульная версия)

## Что реализовано

Проект построен на модульной архитектуре `product/*` и поддерживает:

- CLI-совместимость со старым запуском (`--event`, `--insightId`, `--groups`, `--triggerTime`, `--trigName`, `--message`);
- хранение состояния в PostgreSQL (`alert_state`);
- аудит решений (`alert_state_audit`) с расширенным контекстом;
- историю внешних сущностей (`alert_incidents`);
- интеграции Jira (Assets + создание инцидента + проверка статуса), KTalk (root + thread), AD mapping;
- ночную антифлап-логику 21:00–09:00 с переиспользованием thread/issue в пределах `FLAP_REOPEN_HOURS`.

## Структура

```text
product/
  cnf.py
  logging_setup.py
  main.py
  clients/
    jira_client.py
    ktalk_client.py
    ad_mapping_client.py
  services/
    event_processor.py
    jira_service.py
    ktalk_service.py
    recipient_service.py
    state_service.py
    flap_policy.py
  db/
    connection.py
    queries.py
    repository.py
    schema.py
  models/
    events.py
    state.py
  utils/
    validators.py
    time_utils.py
main.py
```

## Логика жизненного цикла

### `event=1`

1. Ищется `active` state по `insight_id`.
2. Если найден:
   - `event_balance` увеличивается;
   - сообщение пишется в существующий thread;
   - аудит: `append_to_active_incident`.
3. Если не найден:
   - берется `last_state`;
   - если ночь и `now <= flap_reopen_until`, выполняется reuse:
     - state переводится в `active`;
     - новые Jira/KTalk сущности не создаются;
     - сообщение пишется в старый thread;
     - аудит: `reopen_existing_night_incident`.
4. Иначе создаются новые сущности:
   - Jira incident;
   - KTalk root message + first thread reply;
   - запись в `alert_state`;
   - запись в `alert_incidents`;
   - аудит: `open_new_incident` или `night_cooldown_expired_open_new`.

### `event=0`

1. Если активного state нет:
   - событие игнорируется безопасно;
   - аудит: `close_event_ignored_no_state`.
2. Если активный state есть:
   - `event_balance` уменьшается;
   - обновляются `last_event0_at` и `flap_reopen_until`;
   - сообщение отправляется в thread.
3. Если баланс > 0:
   - аудит: `close_event_decrement_only`.
4. Если баланс == 0:
   - **ночью** state переводится в `cooldown_night`, аудит `night_cooldown_started`;
   - **днем** state переводится в `closed`, история инцидента закрывается, аудит `close_final_daytime`.

## Ночная антифлап-логика

- Окно ночи определяется как `hour >= 21 OR hour < 9`.
- На `event=0` вычисляется `flap_reopen_until = event_time + FLAP_REOPEN_HOURS` (в Python, без hardcode в SQL).
- При повторном `event=1` ночью до `flap_reopen_until` открытие идет в существующие `jira_issue_key` и `ktalk_thread_id`.

## Jira

`services/jira_service.py` реализует разбор Assets-атрибутов по `objectTypeAttributeId`:

- `63` → `full_name`
- `126` → `is_actual`
- `2066` → function refs
- `2551` → group id
- `2413` → incident type key

Отдельно извлекаются recipients из атрибутов группы (`2543`, `2542`) + mandatory recipients.

## KTalk

`services/ktalk_service.py` использует `clients/ktalk_client.py` и поддерживает:

- root сообщение как старт обсуждения;
- первый ответ в thread сразу после root;
- отправку сообщений в thread;
- mentions списком;
- нормализацию mention id;
- проверку room members перед invite;
- `KTALK_DRY_RUN_MENTIONS_INVITES`.

## AD mapping

`clients/ad_mapping_client.py` реализует:

- нормализацию логинов;
- чтение профилей получателей из `ad_ktalk_user_map`;
- upsert mapping-записей;
- выдачу `mention_id/full_name` для `RecipientService`.

## База данных

DDL в `product/db/schema.py`:

- `trmetrics.availconf.alert_state`
- `trmetrics.availconf.alert_state_audit` (decision_code, jira_issue_key, ktalk_thread_id, payload_json)
- `trmetrics.availconf.alert_incidents`
- `trmetrics.availconf.ad_ktalk_user_map`

## Пример запуска

```bash
python main.py \
  --event 1 \
  --insightId TZ-12345 \
  --groups "Linux,SG/TEST,..." \
  --triggerTime "2026.04.13 22:15:00" \
  --trigName "CPU load is high" \
  --message "Problem: CPU load is high"
```
