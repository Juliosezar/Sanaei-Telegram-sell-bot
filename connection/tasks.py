from celery import shared_task
from .models import SendMessage, EndOfConfigCounter
from servers.models import CreateConfigQueue, ConfigsInfo, MsgEndOfConfig, Server, TamdidConfigQueue, TestConfig
from servers.views import Configs, ServerApi
from persiantools import jdatetime
from django.conf import settings
from finance.models import ConfirmPaymentQueue, ConfirmTamdidPaymentQueue
import json

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
                    print(name)
                    config_mdl = ConfigsInfo.objects.get(config_name=name)
                    if MsgEndOfConfig.objects.filter(config=config_mdl).exists():
                        if not api[name]["ended"]:
                            if not EndOfConfigCounter.objects.filter(uuid=api[name]["uuid"], type=0).exists():
                                CommandRunner.send_end_of_config_notif(config_mdl.chat_id.userid, api[name])
                                EndOfConfigCounter.objects.create(uuid=api[name]["uuid"], type=0, timestamp=int(jdatetime.JalaliDateTime.now().timestamp())).save()
                        else:
                            if api[name]["usage_limit"] != 0:
                                if (api[name]["usage_limit"] - api[name]["usage"]) < 0.5:
                                    if not EndOfConfigCounter.objects.filter(uuid=api[name]["uuid"], type=1).exists():
                                        CommandRunner.send_almost_end_of_config_notif(config_mdl.chat_id.userid, api[name], 0)
                                        EndOfConfigCounter.objects.create(uuid=api[name]["uuid"], type=1, timestamp=int(jdatetime.JalaliDateTime.now().timestamp())).save()

                            if api[name]["expire_time"] != 0:
                                if (api[name]["expire_time"] * 24) < 13:
                                    if not EndOfConfigCounter.objects.filter(uuid=api[name]["uuid"], type=2).exists():
                                        CommandRunner.send_almost_end_of_config_notif(config_mdl.chat_id.userid, api[name], 1)
                                        EndOfConfigCounter.objects.create(uuid=api[name]["uuid"], type=2, timestamp=int(jdatetime.JalaliDateTime.now().timestamp())).save()

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


@shared_task
def clear_ended_record():
    for obj in EndOfConfigCounter.objects.all():
        delta = int(jdatetime.JalaliDateTime.now().timestamp()) - obj.timestamp
        if delta > 259000:
            obj.delete()

@shared_task
def send_notif_to_admins():
    from connection.command_runer import CommandRunner
    count1 = ConfirmPaymentQueue.objects.filter(status=1).count()
    count2 = ConfirmTamdidPaymentQueue.objects.filter(status=1).count()
    if (count1 + count2) != 0:
        with open(settings.BASE_DIR / 'settings.json', 'r') as f:
            data = json.load(f)
            admins = data["admins_id"]
            for admin in admins:
                CommandRunner.send_msg_to_user(admin, msg=f"{count1 + count2} پرداخت تایید نشده")



@shared_task
def disable_infinit_configs():
    from connection.command_runer import CommandRunner
    for server in Server.objects.all():
        api = ServerApi.get_list_configs(server.server_id)
        if api:
            for name in api:
                if ConfigsInfo.objects.filter(config_name=name).exists():
                    print(name)
                    config_mdl = ConfigsInfo.objects.get(config_name=name)
                    if EndOfConfigCounter.objects.filter(config=config_mdl, type=0).exists():
                        pass
        else:
            pass


@shared_task
def end_of_test_config():
    from connection.command_runer import CommandRunner
    with open(settings.BASE_DIR / "test_server.json", "r") as f:
        data = json.load(f)
        server_id = data["server_id"]
        inbound_id = data["inbound_id"]
        inbound_port = data["inbound_port"]
    for conf in TestConfig.objects.all():
        api = ServerApi.get_config(server_id, conf.config_name)
        if api:
            if not api["ended"]:
                if not conf.sent_notif:
                    CommandRunner.send_msg_to_user(conf.customer.userid, "🔔 کاربر گرامی، کانفیگ تست شما به اتمام رسید." "\n\n" "برای خرید سرویس از طریق منوی اصلی بات یا با پیام به پشتیبانی @NapsV_supp اقدام کنید.")
                    conf.sent_notif = True
                    conf.save()
                api_del = ServerApi.delete_config(server_id, conf.config_uuid, inbound_id)
                if api_del:
                    conf.delete()
