import os

MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'arduino_drive_trainer')
MYSQL_HOST = os.getenv('MYSQLHOST', 'localhost')
MYSQL_USER = os.getenv('MYSQLUSER', 'root')
MYSQL_PASSWORD = os.getenv('MYSQLPASSWORD', '')
MYSQL_PORT = int(os.getenv('MYSQLPORT', 3306))