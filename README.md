# Autoalerter: модульный продукт с ночной антифлап-логикой

## 1. Назначение

Этот репозиторий содержит **новую модульную реализацию autoalerter**, которая:

- принимает событие из CLI (в формате, совместимом со старым запуском);
- ведёт постоянное состояние по `insight_id` в PostgreSQL;
- интегрируется с Jira (Assets + Incident API);
- интегрируется с KTalk (создание корневого сообщения, треды, уведомления);
- реализует ночную антифлап-логику в окне **21:00–09:00**:
  - если после `event=0` повторный `event=1` приходит в пределах 3 часов,
    **новые Jira/KTalk сущности не создаются**;
  - используется предыдущий `jira_issue_key` и предыдущий `ktalk_thread_id`.

---

## 2. Ключевые принципы архитектуры

### 2.1 Разделение ответственности

- `clients/*` — низкоуровневые интеграции (HTTP/LDAP).
- `services/*` — бизнес-логика и orchestration.
- `db/queries.py` — SQL-константы (только SQL).
- `db/repository.py` — доступ к PostgreSQL.
- `models/*` — dataclass-модели событий и состояния.
- `utils/*` — вспомогательные функции (время, валидация).
- `cnf.py` — только конфигурация и константы.

### 2.2 Совместимость с прежним CLI

Запуск поддерживает прежние аргументы:

- `--event`
- `--insightId`
- `--groups`
- `--triggerTime`
- `--trigName`
- `--message`

Корневой `main.py` оставлен как совместимый entrypoint.

### 2.3 Отсутствие `.env`

Все настройки хранятся в Python-конфиге `product/cnf.py`.

---

## 3. Структура проекта

```text
product/
  __init__.py
  main.py
  cnf.py
  logging_setup.py
  models/
    __init__.py
    events.py
    state.py
  db/
    __init__.py
    connection.py
    queries.py
    repository.py
    schema.py
  services/
    __init__.py
    event_processor.py
    state_service.py
    flap_policy.py
    jira_service.py
    ktalk_service.py
    recipient_service.py
  clients/
    __init__.py
    jira_client.py
    ktalk_client.py
    ldap_client.py
  utils/
    __init__.py
    time_utils.py
    validators.py
main.py
README.md
```

---

## 4. Поток обработки события

## 4.1 Общий pipeline

1. `main.py` вызывает `product.main.main()`.
2. `EventProcessor.run_from_cli()` парсит аргументы.
3. Параметры преобразуются в `EventPayload`, затем в `ParsedEvent`.
4. Валидация `insight_id` и разбор времени (`triggerTime`) в timezone-aware datetime.
5. В зависимости от `event` вызывается:
   - `_handle_event_open()` для `event=1`;
   - `_handle_event_close()` для `event=0`.

### 4.2 Логика для `event=1`

1. Проверяется активное состояние по `insight_id`.
2. Если активное состояние уже есть:
   - увеличивается `event_balance`;
   - отправляется сообщение в существующий KTalk thread;
   - пишется аудит (`active_increment`).
3. Если активного состояния нет:
   - берётся последнее состояние (`get_last_state`);
   - проверяется, ночь ли сейчас (21:00–09:00);
   - проверяется условие reuse (`now <= flap_reopen_until`).
4. Если выполняется ночной reuse:
   - состояние реактивируется;
   - **новый Jira issue не создаётся**;
   - **новый KTalk thread не создаётся**;
   - сообщение отправляется в предыдущий тред;
   - пишется аудит (`night_reuse`).
5. Если reuse не подходит:
   - читаются данные сервиса из Jira Assets;
   - при актуальности сервиса создаются:
     - новый Jira Incident,
     - новый KTalk thread,
     - новая запись состояния в БД;
   - пишется аудит (`create_new`).

### 4.3 Логика для `event=0`

1. Ищется активное состояние.
2. Если активного состояния нет:
   - событие безопасно игнорируется;
   - пишется аудит (`ignore_close_no_active`).
3. Если активное состояние есть:
   - уменьшается `event_balance`;
   - обновляются `last_event0_at` и `flap_reopen_until`;
   - отправляется сообщение в текущий thread.
4. Если после уменьшения `event_balance > 0`:
   - состояние остаётся активным;
   - аудит (`decrease_only`).
5. Если `event_balance == 0`:
   - состояние помечается как `closed`;
   - Jira key и thread id в записи сохраняются (для возможного ночного reuse);
   - аудит (`close_state`).

---

## 5. Ночная антифлап-логика (21:00–09:00)

## 5.1 Зачем нужна

При флапах ночью (`1 → 0 → 1`) не нужно плодить инциденты и новые обсуждения, если повторное открытие произошло вскоре после закрытия.

### 5.2 Условия reuse

Reuse старого контекста (issue/thread) выполняется, когда одновременно соблюдены условия:

- текущее событие попадает в ночное окно `21:00–09:00`;
- активного состояния сейчас нет;
- существует предыдущее состояние по `insight_id`;
- у предыдущего состояния есть `last_event0_at`;
- у предыдущего состояния есть `flap_reopen_until`;
- текущее время `<= flap_reopen_until`.

### 5.3 Как считается окно

- ночное окно проверяется через правило: `hour >= 21 OR hour < 9`;
- `flap_reopen_until` выставляется в БД на этапе `event=0` как `event_time + interval '3 hours'`.

### 5.4 Что происходит при reuse

- выполняется `ACTIVATE_EXISTING_STATE`;
- сообщение отправляется в существующий `ktalk_thread_id`;
- используются прежние `jira_issue_key` и thread;
- новые внешние сущности **не создаются**.

---

## 6. Конфигурация (`product/cnf.py`)

В конфиге находятся:

- параметры подключения к PostgreSQL;
- Jira URL и токены;
- KTalk URL, токен, room-id и поведение dry-run;
- таймауты и SSL-флаг;
- путь к лог-файлу;
- параметры антифлап-логики:
  - `FLAP_NIGHT_START_HOUR = 21`
  - `FLAP_NIGHT_END_HOUR = 9`
  - `FLAP_REOPEN_HOURS = 3`
  - `TIMEZONE_NAME = "Europe/Moscow"`

> Рекомендуется вынести секреты в защищённый способ доставки конфигурации на уровне runtime/CI/CD, но интерфейс модуля `cnf.py` оставить прежним.

---

## 7. Работа с PostgreSQL

## 7.1 Где лежит SQL

Все SQL-запросы находятся в `product/db/queries.py`.

### 7.2 Где лежит доступ к БД

`product/db/repository.py` реализует методы:

- `get_active_state`
- `get_last_state`
- `create_state`
- `activate_existing_state`
- `decrease_event_balance`
- `mark_state_closed`
- `append_audit_event`

### 7.3 Схема таблиц

DDL расположен в `product/db/schema.py`:

- `trmetrics.availconf.alert_state` — текущее/последнее состояние по алерту;
- `trmetrics.availconf.alert_state_audit` — журнал действий процессора.

Ключевые поля `alert_state`:

- `event_balance`
- `status`
- `last_event1_at`
- `last_event0_at`
- `flap_reopen_until`
- `ktalk_thread_id`
- `jira_issue_key`

---

## 8. Интеграции

## 8.1 Jira

- `clients/jira_client.py` — HTTP-вызовы Jira.
- `services/jira_service.py` — подготовка/интерпретация данных:
  - получение сервисных атрибутов;
  - создание инцидента;
  - проверка статуса issue.

### 8.2 KTalk

- `clients/ktalk_client.py` — HTTP API KTalk.
- `services/ktalk_service.py` — бизнес-функции:
  - создание обсуждения (`event_id` первого сообщения используется как `thread_id`);
  - отправка сообщений в thread;
  - уведомление получателей и инвайт (если включено).

### 8.3 AD / Recipients

- `clients/ldap_client.py` — базовый LDAP-адаптер.
- `services/recipient_service.py` — преобразование списка получателей в mention-id.

---

## 9. Логирование

`product/logging_setup.py` настраивает единый logger `autoalerter` с записью в файл из `cnf.LOG_FILE`.

Рекомендуется подключать ротацию логов на уровне окружения (systemd/journald/logrotate).

---

## 10. Примеры запуска

### 10.1 Problem (`event=1`)

```bash
python main.py \
  --event 1 \
  --insightId TZ-12345 \
  --groups "Linux,SG/TEST,..." \
  --triggerTime "2026.04.13 22:15:00" \
  --trigName "CPU load is high" \
  --message "Problem: CPU load is high"
```

### 10.2 Recovery (`event=0`)

```bash
python main.py \
  --event 0 \
  --insightId TZ-12345 \
  --groups "Linux,SG/TEST,..." \
  --triggerTime "2026.04.13 23:05:00" \
  --trigName "CPU load is high" \
  --message "Recovery: CPU load is normal"
```

---

## 11. Проверка сценариев (чек-лист)

При ручной/интеграционной проверке рекомендуется подтвердить:

1. Днём `event=1` без active state → создаются новый Jira и новый thread.
2. Повторный `event=1` при active state → запись в текущий thread, без новых внешних сущностей.
3. `event=0` при active state → уменьшается баланс, обновляется `last_event0_at`.
4. Ночью `event=1` в пределах 3 часов после `event=0` → reuse предыдущих Jira/thread.
5. Ночью `event=1` позже 3 часов → создаются новые Jira/thread.
6. Днём `event=1` после закрытия → стандартное создание новой сущности.
7. `event=0` без active state → корректный ignore без падения.

---

## 12. Примечания по эксплуатации

- Перед запуском убедитесь, что в PostgreSQL существуют схемы/права для `trmetrics.availconf`.
- Примените DDL из `product/db/schema.py` до старта процессора.
- Для production лучше использовать отдельного DB-пользователя с минимально достаточными правами.
- Для внешних API настройте доступность endpoint'ов и корректные токены в `cnf.py`.
