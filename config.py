import os
SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Connect to the database
# DB Connection variables
db_driver = 'postgresql'
username = 'postgres'
password = 'root'
host_address = 'localhost'
port = '5432'
dbname = 'fyyur'

# TODO IMPLEMENT DATABASE URL
SQLALCHEMY_DATABASE_URI = db_driver + "://" + username + ":" + password + "@" + host_address + ":" + port + "/" + dbname
SQLALCHEMY_TRACK_MODIFICATIONS = False
