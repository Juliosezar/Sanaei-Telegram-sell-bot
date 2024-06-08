import pymysql
from .celery_conf import celery_app
pymysql.install_as_MySQLdb()
