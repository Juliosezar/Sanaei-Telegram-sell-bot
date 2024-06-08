from celery import shared_task
from .models import SendMessage
from servers.models import CreateConfigQueue
from servers.views import Configs
@shared_task
def send_msg_to_bot():
    from connection.command_runer import CommandRunner
    msgs = SendMessage.objects.filter(status__in=['Faild', 'Created', 'Timeout'])
    if msgs.exists():
        for msg in msgs:
            obj = SendMessage.objects.get(uuid=msg.uuid)
            obj.status = 'Pending'
            obj.save()
            respons = CommandRunner.celery_send_msg(msg.customer.userid, msg.message)
            obj.status = respons
            obj.save()

@shared_task
def create_config():
    obj = CreateConfigQueue.objects.filter(sent_to_user=5)
    if obj.exists():
        for conf in obj:
            Configs.create_config_from_queue(config_uuid=conf.config_uuid, by_celery=True)