import os

MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'railway')
MYSQL_HOST = os.getenv('MYSQLHOST', 'mysql.railway.internal')
MYSQL_USER = os.getenv('MYSQLUSER', 'root')
MYSQL_PASSWORD = os.getenv('MYSQLPASSWORD', 'UOuEJWSEEnxequxLBWBNeRrWHDpuShit')
MYSQL_PORT = int(os.getenv('MYSQLPORT', 3306))