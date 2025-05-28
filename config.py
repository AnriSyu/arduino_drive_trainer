# config.py
import pymysql

db_config = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "arduino_drive_trainer",
    'cursorclass': pymysql.cursors.DictCursor
}
