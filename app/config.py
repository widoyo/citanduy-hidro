from os import environ

DBUSER = environ.get('DB_USER')
DBNAME = environ.get('DB_NAME')
DBPORT = environ.get('DB_PORT')
DBHOST = environ.get('DB_HOST')
DBPASS = environ.get('DB_PASSWORD')
SECRET_KEY = environ.get('SECRET')
SOURCE_A = environ.get('SDATELEMETRY_URL')
SOURCE_B = environ.get('TELEMET_URL')
SOURCE_C = environ.get('LUWES_URL')
SDATELEMETRY_POS_EXCLUDES = environ.get('SDATELEMETRY_POS_EXCLUDES')

BOT_TOKEN = environ.get('BOT_TOKEN')
CTY_OFFICE_ID = environ.get('CTY_KANTOR_ID')

DATABASE = {
    'engine': 'playhouse.pool.PooledPostgresqlDatabase',
    'name': DBNAME,
    'user': DBUSER,
    'password': DBPASS,
    'host': DBHOST,
    'max_connections': 32,
    'stale_timeout': 600,
}
