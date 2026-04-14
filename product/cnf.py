"""Configuration constants for autoalerter product."""

DB_HOST = "localhost"
DB_NAME = "trmetrics"
DB_USER = "user"
DB_PASSWORD = "password"
DB_PORT = 5432
DB_OPTIONS = ""

JIRA_TOKEN = "Bearer <token>"
JIRA_SERVICE_URL = "https://hd.samoletgroup.ru/rest/assets/1.0/object/{}/attributes"
JIRA_CREATE_INC_URL = "https://hd-dev02.samoletgroup.ru/rest/api/2/issue"
JIRA_ISSUE_STATUS_URL = "https://hd-dev02.samoletgroup.ru/rest/api/2/issue/{}?fields=status"
JIRA_ISSUE_BROWSE_URL = "https://hd-dev02.samoletgroup.ru/browse/{}"

KTALK_BASE_URL = "https://chat.ktalk.ru"
KTALK_BOT_USER = "zabbix_bot"
KTALK_JWT_TOKEN = "<ktalk_bot_jwt_token>"
KTALK_ROOM_ID = "!room:matrix-9.ktalk.ru"
KTALK_USER_DOMAIN = "matrix-9.ktalk.ru"
KTALK_DRY_RUN_MENTIONS_INVITES = False

REQUEST_TIMEOUT = 30
VERIFY_SSL = False
LOG_FILE = "/tmp/autoalerter.log"

FLAP_NIGHT_START_HOUR = 21
FLAP_NIGHT_END_HOUR = 9
FLAP_REOPEN_HOURS = 3
TIMEZONE_NAME = "Europe/Moscow"
