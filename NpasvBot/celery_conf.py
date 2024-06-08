from celery import Celery
from datetime import timedelta
from os import environ


environ.setdefault('DJANGO_SETTINGS_MODULE', 'NpasvBot.settings')

celery_app = Celery('NpasvBot')

celery_app.conf.broker_connection_retry_on_startup = True
celery_app.autodiscover_tasks()
# celery_app.conf.broker_url = 'amqp://'
celery_app.conf.broker_url = 'amqp://sezar:1223@localhost:5672//'
celery_app.conf.result_backend = 'rpc://'
celery_app.conf.task_serializer = 'json'
