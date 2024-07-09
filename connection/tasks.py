from celery import shared_task
from .models import SendMessage, EndOfConfigCounter
from servers.models import CreateConfigQueue, ConfigsInfo, Server, TamdidConfigQueue, TestConfig
from servers.views import Configs, ServerApi, InfinitCongisLimit
from persiantools import jdatetime
from django.conf import settings
from finance.models import ConfirmPaymentQueue, ConfirmTamdidPaymentQueue
import json
from reports.views import Log
from custumers.models import Customer


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
def send_end_conf_notif(): # and delete ended confs after 3 days
    from connection.command_runer import CommandRunner
    for server in Server.objects.all():
        api = ServerApi.get_list_configs(server.server_id)
        if api:
            for name in api:
                if ConfigsInfo.objects.filter(config_name=name).exists():
                    config_mdl = ConfigsInfo.objects.get(config_name=name)
                    if not api[name]["ended"]:
                        if not EndOfConfigCounter.objects.filter(config=config_mdl, type=0).exists():
                            if config_mdl.chat_id:
                                CommandRunner.send_end_of_config_notif(config_mdl.chat_id.userid, api[name])
                            EndOfConfigCounter.objects.create(config=config_mdl, type=0, timestamp=int(jdatetime.JalaliDateTime.now().timestamp())).save()
                        else:

                            counter_obj = EndOfConfigCounter.objects.get(config=config_mdl, type=0)
                            if (int(jdatetime.JalaliDateTime.now().timestamp()) - counter_obj.timestamp) > 259200:
                                delete = ServerApi.delete_config(config_mdl.server.server_id, config_mdl.config_uuid, api[name]["inbound_id"])
                                if delete:
                                    userid = 0
                                    if config_mdl.chat_id:
                                        CommandRunner.send_msg_to_user(config_mdl.chat_id.userid, f"🔴 سرویس {name} حذف شد و امکان تمدید آن وجود ندارد. میتوانید از بخش خرید سرویس در منوی اصلی یا با ارتباط با ادمین اقدام به خرید سرویس جدید کنید.")
                                        Log.create_customer_log(Customer.objects.get(userid=config_mdl.chat_id.userid), f"❌ Delete \"{name}\" by \"Celery\"")
                                        userid = config_mdl.chat_id.userid
                                    config_mdl.delete()
                                    cel = "(End Time)" if api[name]["expired"] else "(End Usage)"
                                    Log.celery_delete_conf_log(f"❌ Delete \"{name}\" - {cel}", userid)
                                    Log.create_admin_log("Celery", f"❌ Delete \"{name}\"")

                    else:
                        if api[name]["usage_limit"] != 0:
                            if (api[name]["usage_limit"] - api[name]["usage"]) < 0.5:
                                if not EndOfConfigCounter.objects.filter(config=config_mdl, type=1).exists():
                                    if config_mdl.chat_id:
                                        CommandRunner.send_almost_end_of_config_notif(config_mdl.chat_id.userid, api[name], 0)
                                    EndOfConfigCounter.objects.create(config=config_mdl, type=1, timestamp=int(jdatetime.JalaliDateTime.now().timestamp())).save()
                        if api[name]["expire_time"] != 0:
                            if (api[name]["expire_time"] * 24) < 13:
                                if not EndOfConfigCounter.objects.filter(config=config_mdl, type=2).exists():
                                    if config_mdl.chat_id:
                                        CommandRunner.send_almost_end_of_config_notif(config_mdl.chat_id.userid, api[name], 1)
                                    EndOfConfigCounter.objects.create(config=config_mdl, type=2, timestamp=int(jdatetime.JalaliDateTime.now().timestamp())).save()


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
        if delta > 345600:
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
                if InfinitCongisLimit.objects.filter(config__config_uuid=api[name]["uuid"]).exists() and api[name]["usage_limit"] == 0 and api[name]["enable"] and api[name]["ended"]:
                    inf_obj = InfinitCongisLimit.objects.get(config__config_uuid=api[name]["uuid"])
                    if inf_obj.limit < int(api[name]["usage"]):
                        if int(api[name]["expire_time"]) > 4:
                            session = ServerApi.create_session(server_id=server.server_id)
                            if session:
                                time_expire = int((abs(api[name]["expire_time"] * 86400000)) * -1)
                                ServerApi.disable_config(session, server.server_id, api[name]["uuid"], api[name]["inbound_id"], name, True, api[name]["ip_limit"], time_expire, 0)
                                CommandRunner.send_msg_to_user(inf_obj.config.chat_id.userid, f" 🔴 سرویس {name} توسط سیستم غیرفعال شد.")
                                Log.create_config_log(inf_obj.config, f"⛔ Disable \"{name}\" by \"Celery\"")
                                Log.create_admin_log("Celery", f"⛔ Disable \"{name}\"")
                                Log.celery_delete_conf_log(f"⛔ Disable \"{name}\"", inf_obj.config.chat_id.userid)
                                if inf_obj.config.chat_id:
                                    Log.create_customer_log(inf_obj.config.chat_id, f"⛔ Disable \"{name}\" by \"Celery\"")

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
