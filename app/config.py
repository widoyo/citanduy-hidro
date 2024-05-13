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