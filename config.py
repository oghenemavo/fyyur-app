import os
SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = os.getenv('DEBUG')

# Connect to the database
# DB Connection variables
db_driver = os.getenv('DB_DRIVER')
username = os.getenv('USERNAME')
password = os.getenv('PASSWORD')
host_address = os.getenv('HOST_ADDRESS')
port = os.getenv('PORT')
dbname = os.getenv('DBNAME')

# TODO IMPLEMENT DATABASE URL
SQLALCHEMY_DATABASE_URI = db_driver + "://" + username + ":" + password + "@" + host_address + ":" + port + "/" + dbname
SQLALCHEMY_TRACK_MODIFICATIONS = False
