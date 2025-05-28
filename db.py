# db.py
import pymysql
from config import db_config

def get_connection():
    return pymysql.connect(**db_config)
