from celery import shared_task
from .models import SendMessage, EndOfConfigCounter
from servers.models import CreateConfigQueue, ConfigsInfo, MsgEndOfConfig, Server, TamdidConfigQueue
from servers.views import Configs, ServerApi
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

@shared_task
def send_end_conf_notif():
    from connection.command_runer import CommandRunner
    for server in Server.objects.all():
        api = ServerApi.get_list_configs(server.server_id)
        if api:
            for name in api:
                if ConfigsInfo.objects.filter(config_name=name).exists():
                    config_mdl = ConfigsInfo.objects.get(config_name=name)
                    if MsgEndOfConfig.objects.filter(config=config_mdl).exists():
                        if not api[name]["ended"]:
                            if not EndOfConfigCounter.objects.filter(uuid=api[name]["uuid"], type=0).exists():
                                CommandRunner.send_end_of_config_notif(config_mdl.chat_id.userid, api[name])
                                EndOfConfigCounter.objects.create(uuid=api[name]["uuid"], type=0).save()
                        else:
                            if api[name]["usage_limit"] != 0:
                                if (api[name]["usage_limit"] - api[name]["usage"]) < 0.5:
                                    if not EndOfConfigCounter.objects.filter(uuid=api[name]["uuid"], type=1).exists():
                                        CommandRunner.send_almost_end_of_config_notif(config_mdl.chat_id.userid, api[name], 0)
                                        EndOfConfigCounter.objects.create(uuid=api[name]["uuid"], type=1).save()

                            if api[name]["expire_time"] != 0:
                                if (api[name]["expire_time"] * 24) < 13:
                                    if not EndOfConfigCounter.objects.filter(uuid=api[name]["uuid"], type=2).exists():
                                        CommandRunner.send_almost_end_of_config_notif(config_mdl.chat_id.userid, api[name], 1)
                                        EndOfConfigCounter.objects.create(uuid=api[name]["uuid"], type=2).save()

                    else:
                        MsgEndOfConfig.objects.create(config=config_mdl)
        else:
            pass
        #TODO : log errors


@shared_task
def tamdid_config():
    obj = TamdidConfigQueue.objects.filter(sent_to_user=5)
    if obj.exists():
        for conf in obj:
            Configs.tamdid_config_from_queue(config_uuid=conf.config.config_uuid, by_celery=True)




