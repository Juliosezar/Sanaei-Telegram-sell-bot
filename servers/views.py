import datetime
import uuid
from binary import BinaryUnits, convert_units
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View
from binary import BinaryUnits, convert_units

from .models import Server as ServerModel, ConfigsInfo
import requests
from django.conf import settings
import json
from servers.models import CreateConfigQueue
import random
import string
from custumers.models import Customer as CustomerModel
def change_wallet_amount(user_id, amount):
    model_obj = CustomerModel.objects.get(userid=user_id)
    model_obj.wallet = model_obj.wallet + amount
    model_obj.save()


class ServerApi:
    @classmethod
    def create_session(cls, server_id):
        server_obj = ServerModel.objects.get(server_id=server_id)
        server_url = server_obj.server_url
        incound_id = server_obj.inbound_id
        login_payload = {"username": server_obj.username, "password": server_obj.password}
        login_url = server_url + "login/"
        header = {"Accept": "application/json"}
        session = requests.Session()
        login_response = session.post(login_url, headers=header, json=login_payload, timeout=15)
        if login_response.status_code == 200:
            if login_response.json()["success"]:
                return session
        else:
            return False

    @classmethod
    def get_list_configs(cls, server_id):
        server_obj = ServerModel.objects.get(server_id=server_id)
        session = cls.create_session(server_id)
        list_configs = session.get(server_obj.server_url + "panel/api/inbounds/list/", timeout=15)
        joined_data = {}
        for respons in list_configs.json()["obj"]:
            for i in respons["clientStats"]:

                expired = False
                started = True
                presentDate = datetime.datetime.now()
                unix_timestamp = datetime.datetime.timestamp(presentDate) * 1000
                time_expire = i["expiryTime"]
                if time_expire > 0:
                    time_expire = int((time_expire - unix_timestamp) / 86400000)
                    if time_expire < 0:
                        expired = True
                        time_expire = abs(time_expire)
                elif time_expire == 0:
                    time_expire = "&infin;"
                    if i['usage'] == 0:
                        started = False
                else:
                    time_expire = abs(int(time_expire / 86400000))
                    started = False

                usage = round(convert_units(i["up"] + i["down"], BinaryUnits.BYTE, BinaryUnits.GB)[0], 2)
                total_usage = int(convert_units(i['total'], BinaryUnits.BYTE, BinaryUnits.GB)[0])
                joined_data[i["email"]] = {
                    'enable': i["enable"],
                    'usage': usage,
                    'started': started,
                    'expire_time': time_expire,
                    'usage_limit': total_usage,
                    'inbound_id': i["inboundId"]
                }
            for i in json.loads(respons["settings"])["clients"]:
                joined_data[i["email"]]['uuid'] = i["id"]
                joined_data[i["email"]]['ip_limit'] = i["limitIp"]
        print(joined_data)
        return joined_data

    @classmethod
    def create_config(cls, server_id, config_name, uid, usage_limit_GB, expire_DAY, ip_limit, enable):
        server_obj = ServerModel.objects.get(server_id=server_id)
        url = server_obj.server_url + "panel/api/inbounds/addClient"
        expire_time = int(expire_DAY) * 24 * 60 * 60 * 1000 * -1
        usage_limit = int(convert_units(usage_limit_GB, BinaryUnits.GB, BinaryUnits.BYTE)[0])
        setting = {
            'clients': [{
                'id': str(uid), 'alterId': 0, 'email': config_name,
                'limitIp': ip_limit, 'totalGB': usage_limit,
                'expiryTime': expire_time, 'enable': enable,
                "tgId": '', 'subId': ''
            }]
        }
        data1 = {
            "id": int(server_obj.inbound_id),
            "settings": json.dumps(setting)
        }
        header = {"Accept": "application/json"}
        print("11111")
        session = cls.create_session(server_id)
        if not session:
            return False
        respons = session.post(url, headers=header, json=data1)
        print(respons.content)
        if respons.status_code == 200:
            if respons.json()['success']:
                return True
        return False


    @classmethod
    def get_config(cls, server_id, config_name):
        server_obj = ServerModel.objects.get(server_id=server_id)
        url = server_obj.server_url + f"panel/api/inbounds/getClientTraffics/{config_name}"
        session = cls.create_session(server_id)
        if not session:
            return False
        respons = session.get(url)
        if respons.status_code == 200:
            if respons.json()['success']:
                obj = respons.json()["obj"]
                print(obj)
                return {
                    'enable' : obj["enable"],
                    'expiryTime' : obj["expiryTime"],
                    'usage' : obj["up"] + obj["down"],
                    'usage_limit': obj["total"]
                }
        return False


class Configs:

    @classmethod
    def save_config_info(cls, config_name, config_uuid, server, chat_id):
        ConfigsInfo.objects.create(
            config_name=config_name,
            config_uuid=config_uuid,
            server=ServerModel.objects.get(server_id=server),
            chat_id=CustomerModel.objects.get(userid=chat_id)
        ).save()

    @classmethod
    def create_vless_text(cls, config_uuid, server_obj, config_name):
        vless = ('📡 کانفیگ شما:' '\n\n'
                 f"`vless://{config_uuid}@{server_obj.server_fake_domain}:{server_obj.inbound_port}?"
                 f"type=tcp&path=%2F&host=speedtest.net&headerType=http&security=none#{config_name}`"
                 '\n' 'برای کپی کردن کانفیگ روی متن بالا کلیک کنید.'
                 f'\n\n' '🚀ربات مشاهده حجم و روز در تلگرام:' '\n' f'bot link' '\n\n' f'🏁 کیو آر کد (QrCode):' '\n' f'qrcodelink'
                 )
        return vless

    @classmethod
    def send_config_to_user(cls, user_id, config_uuid, server, config_name):
        from connection.command_runer import CommandRunner
        server_obj = ServerModel.objects.get(server_id=server)
        vless = cls.create_vless_text(config_uuid, server_obj, config_name)
        CommandRunner.send_notification(user_id, vless)
    @classmethod
    def add_configs_to_queue_before_confirm(cls, server_id, user_id, config_uuid, usage_limit, expire_time, user_limit,
                                            price):
        user_obj = CustomerModel.objects.get(userid=user_id)
        if CreateConfigQueue.objects.filter(custumer=user_obj, pay_status=0).exists():
            CreateConfigQueue.objects.get(custumer=user_obj, pay_status=0).delete()

        CreateConfigQueue.objects.create(
            custumer=user_obj,
            server=ServerModel.objects.get(server_id=server_id),
            config_uuid=config_uuid,
            config_name=Configs.generate_unique_name(),
            usage_limit=usage_limit,
            expire_time=expire_time,
            user_limit=user_limit,
            price=price
        ).save()

    @staticmethod
    def generate_unique_name():
        characters = string.digits + string.ascii_uppercase
        unique_number = ''.join(random.choice(characters) for _ in range(6))
        return unique_number

    @classmethod
    def create_config_from_queue(cls, config_uuid):
        from connection.command_runer import CommandRunner
        config_queue_obj = CreateConfigQueue.objects.get(config_uuid=config_uuid)
        respons = ServerApi.create_config(
            server_id=config_queue_obj.server.server_id,
            config_name=config_queue_obj.config_name,
            uid=config_uuid,
            usage_limit_GB=config_queue_obj.usage_limit,
            expire_DAY=config_queue_obj.expire_time,
            ip_limit=config_queue_obj.user_limit,
            enable=True,
        )
        if respons:
            change_wallet_amount(config_queue_obj.custumer.userid, -1 * config_queue_obj.price)
            cls.send_config_to_user(config_queue_obj.custumer.userid, config_uuid,
                                    config_queue_obj.server.server_id, config_queue_obj.config_name)
            cls.save_config_info(config_queue_obj.config_name, config_queue_obj.config_uuid,
                                 config_queue_obj.server.server_id, config_queue_obj.custumer.userid)
        else:
            CommandRunner.send_notification(config_queue_obj.custumer.userid,
            '🟢 کابر گرامی سرورها در حال آپدیت هستند و کانفیگ شما با کمی تاخیر بعد از اتمام آپدیت برای شما ارسال میشود.')


    @classmethod
    def create_config_from_wallet(cls,chat_id, server_id, expire_limit, usage_limit, user_limit, price):
        from connection.command_runer import CommandRunner
        server_obj = ServerModel.objects.get(server_id=server_id)
        conf_uuid = str(uuid.uuid4())
        config_name = Configs.generate_unique_name()
        create_config = ServerApi.create_config(server_id, config_name, conf_uuid, usage_limit, expire_limit *30, user_limit, True)
        if create_config:
            vless = cls.create_vless_text(conf_uuid, server_obj, config_name)
            CommandRunner.send_notification(chat_id, vless)
            change_wallet_amount(chat_id,-1 * price)
            cls.save_config_info(config_name, conf_uuid, server_id, chat_id)
            return True
        return False


class ListConfigs( View):
    def get(self, request,server_id, *args, **kwargs):
        server_model = ServerModel.objects.get(server_id=server_id)
        ServerApi.get_list_configs(server_id)

