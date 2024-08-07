import datetime
import uuid
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.views import View
from binary import BinaryUnits, convert_units
from django.db.models import Q
from .models import Server as ServerModel, ConfigsInfo
import requests
import json
from servers.models import CreateConfigQueue, TamdidConfigQueue, TestConfig, InfinitCongisLimit
from custumers.models import Customer as CustomerModel
from .forms import SearchForm, CreateConfigForm, ManualCreateConfigForm, ChangeConfigSettingForm, AddServerForm, \
    EditServerForm, ChangeConfigLocForm, ChangeUnlimitConfLimitForm
from django.contrib import messages
from accounts.forms import SearchConfigForm
from finance.models import Prices as PricesModel
from rest_framework.views import APIView
from rest_framework.response import Response
from time import sleep
from os import environ
from reports.views import Log
from reports.models import ConfigLog
from django.conf import settings
from finance.models import UserActiveOffCodes
import re

BOT_USERNAME = environ.get('BOT_USERNAME')


def change_wallet_amount(user_id, amount):
    model_obj = CustomerModel.objects.get(userid=user_id)
    model_obj.wallet = model_obj.wallet + amount
    model_obj.save()

def extract_domain(url):
    pattern = r'(?:https?:\/\/)?(?:[^@\n]+@)?(?:www\.)?([^:\/\n?]+)'
    match = re.search(pattern, url)
    return match.group(1) if match else None


class ServerApi:
    @classmethod
    def create_session(cls, server_id):
        server_obj = ServerModel.objects.get(server_id=server_id)
        server_url = server_obj.server_url
        incound_id = server_obj.inbound_id
        login_payload = {"username": server_obj.username, "password": server_obj.password}
        login_url = server_url + "login/"
        header = {"Accept": "application/json"}
        try:
            session = requests.Session()
            login_response = session.post(login_url, headers=header, json=login_payload, timeout=15)
            if login_response.status_code == 200:
                if login_response.json()["success"]:
                    return session
            else:
                session.close()
                return False
        except Exception as e:
            return False

    @classmethod
    def get_list_configs(cls, server_id):
        try:
            server_obj = ServerModel.objects.get(server_id=server_id)
            session = cls.create_session(server_id)
            if not session:
                return False
            list_configs = session.get(server_obj.server_url + "panel/api/inbounds/list/", timeout=15)
            if list_configs.status_code != 200:
                session.close()
                return False
            joined_data = {}
            for respons in list_configs.json()["obj"]:
                if respons["id"] == server_obj.inbound_id:
                    for i in respons["clientStats"]:
                        expired = False
                        started = True
                        presentDate = datetime.datetime.now()
                        unix_timestamp = datetime.datetime.timestamp(presentDate) * 1000
                        time_expire = i["expiryTime"]
                        if time_expire > 0:
                            time_expire = (time_expire - unix_timestamp) / 86400000
                            if time_expire < 0:
                                expired = True

                        elif time_expire == 0:
                            if i['down'] + i["up"] == 0:
                                started = False
                        else:
                            time_expire = abs(int(time_expire / 86400000))
                            started = False

                        usage = round(convert_units(i["up"] + i["down"], BinaryUnits.BYTE, BinaryUnits.GB)[0], 2)
                        started = True if usage > 0 else False
                        total_usage = int(convert_units(i['total'], BinaryUnits.BYTE, BinaryUnits.GB)[0])
                        total_usage = 0 if total_usage < 0 else total_usage
                        joined_data[i["email"]] = {
                            'ended': i["enable"],
                            'usage': usage,
                            'started': started,
                            'expire_time': time_expire,
                            'usage_limit': total_usage,
                            'inbound_id': i["inboundId"],
                            "expired": expired
                        }
                    for i in json.loads(respons["settings"])["clients"]:
                        joined_data[i["email"]]['uuid'] = i["id"]
                        joined_data[i["email"]]['ip_limit'] = i["limitIp"]
                        joined_data[i["email"]]['enable'] = i["enable"]
            session.close()
            return joined_data
        except Exception as e:
            return False

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
        try:
            session = cls.create_session(server_id)
            if not session:
                return False
            respons = session.post(url, headers=header, json=data1, timeout=6)
            if respons.status_code == 200:
                if respons.json()['success']:
                    session.close()
                    return True
            session.close()
            return False
        except Exception as e:
            return False

    @classmethod
    def renew_config(cls, server_id, config_uuid, config_name, expire_time, total_usage, ip_limit, reset=True):
        server_obj = ServerModel.objects.get(server_id=server_id)
        url = server_obj.server_url + "panel/api/inbounds"
        expire_time = (int(expire_time) * 24 * 60 * 60 * 1000 * -1)
        total_usage = (int(convert_units(int(total_usage), BinaryUnits.GB, BinaryUnits.BYTE)[0]))
        setting = {
            'clients': [{
                'id': str(config_uuid), 'alterId': 0, 'email': config_name,
                'limitIp': ip_limit, 'totalGB': total_usage,
                'expiryTime': expire_time, 'enable': True,
                "tgId": '', 'subId': ''
            }]
        }
        data1 = {
            "id": int(server_obj.inbound_id),
            "settings": json.dumps(setting)
        }
        header = {"Accept": "application/json"}

        try:
            session = cls.create_session(server_id)
            if not session:
                return False
            respons = session.post(url + f"/updateClient/{str(config_uuid)}/", headers=header, json=data1, timeout=6)
            if reset:
                respons2 = session.post(url + f"/{server_obj.inbound_id}/resetClientTraffic/{config_name}/", headers={},
                                        data={}, timeout=6)
                if not respons2.status_code == 200:
                    session.close()
                    return False
            if respons.status_code == 200:
                if respons.json()['success']:
                    session.close()
                    return True
            session.close()
            return False
        except Exception as e:
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
                if obj:
                    expired = False
                    started = True
                    presentDate = datetime.datetime.now()
                    unix_timestamp = datetime.datetime.timestamp(presentDate) * 1000
                    time_expire = obj["expiryTime"]
                    if time_expire > 0:
                        time_expire = (time_expire - unix_timestamp) / 86400000
                        if time_expire < 0:
                            expired = True
                    elif time_expire == 0:
                        if obj['down'] + obj["up"] == 0:
                            started = False
                    else:
                        time_expire = abs(int(time_expire / 86400000))
                        started = False
                    usage = round(convert_units(obj["up"] + obj["down"], BinaryUnits.BYTE, BinaryUnits.GB)[0], 2)
                    started = True if usage > 0 else False
                    total_usage = int(convert_units(obj['total'], BinaryUnits.BYTE, BinaryUnits.GB)[0])
                    total_usage = 0 if total_usage < 0 else total_usage
                    session.close()
                    return {
                        'ended': obj["enable"],
                        'time_expire': time_expire,
                        'usage': usage,
                        'usage_limit': total_usage,
                        'started': started,
                        'exp_time_sta': expired,
                        'inbound_id': int(obj["inboundId"]),
                        "expired": expired
                    }
        session.close()
        return False

    @classmethod
    def change_location(cls, from_server_id, to_server_id, config_uuid):
        config_obj = ConfigsInfo.objects.get(config_uuid=config_uuid)
        from_server_obj = ServerModel.objects.get(server_id=from_server_id)
        from_session = cls.create_session(from_server_id)

        to_server_obj = ServerModel.objects.get(server_id=to_server_id)
        to_session = cls.create_session(to_server_id)

        if not from_session or not to_session:
            return False
        list_configs = from_session.get(from_server_obj.server_url + "panel/api/inbounds/list/", timeout=15)
        if list_configs.status_code != 200:
            from_session.close()
            return False
        joined_data = {}
        for i in list_configs.json()["obj"]:
            for ii in i["clientStats"]:
                if ii["email"] == config_obj.config_name:
                    joined_data["total_usage"] = ii["total"]
                    joined_data["usage"] = ii["up"] + ii["down"]
                    joined_data["time_expire"] = ii["expiryTime"]
                    joined_data["ended"] = ii["enable"]
                    break
            for ii in json.loads(i["settings"])["clients"]:
                if ii["email"] == config_obj.config_name:
                    joined_data["enable"] = ii["enable"]
                    joined_data["ip_limit"] = ii["limitIp"]
                    break
        if not joined_data["ended"] or not joined_data["enable"]:
            return "ended"
        url = to_server_obj.server_url + "panel/api/inbounds/addClient"
        setting = {
            'clients': [{
                'id': str(config_obj.config_uuid), 'alterId': 0, 'email': config_obj.config_name,
                'limitIp': joined_data["ip_limit"], 'totalGB': joined_data["total_usage"] - joined_data["usage"],
                'expiryTime': joined_data["time_expire"], 'enable': joined_data["enable"],
                "tgId": '', 'subId': ''
            }]
        }
        data1 = {
            "id": int(to_server_obj.inbound_id),
            "settings": json.dumps(setting)
        }
        header = {"Accept": "application/json"}
        try:
            respons2 = to_session.post(url, headers=header, json=data1, timeout=6)
            if respons2.status_code == 200:
                if respons2.json()['success']:
                    url = from_server_obj.server_url + f"panel/api/inbounds/{from_server_obj.inbound_id}/delClient/{config_uuid}"
                    respons3 = from_session.post(url)
                    if respons3.status_code == 200:
                        if respons3.json()['success']:
                            from_session.close()
                            return True
                    to_session.close()
                    return False
            to_session.close()
            return False
        except Exception as e:
            return False

    @classmethod
    def backup(cls, server):
        import paramiko
        import socket

        domain = extract_domain(server.server_url)
        try:
            SSH_Client = paramiko.SSHClient()
            SSH_Client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            SSH_Client.connect(hostname=domain, username="root", password=server.password, look_for_keys=False, timeout=2)
            sftp_client = SSH_Client.open_sftp()
            localFilePath = "/home/sezar/tmp/sf2.db"
            remoteFilePath = "/etc/x-ui/x-ui.db"

            sftp_client.get(remoteFilePath, localFilePath)
            sftp_client.close()
            return True
        except paramiko.SSHException as e:
            print(f"SSH Exception: {e}")
            return False
        except socket.error as e:
            print(f"Socket error: {e}")
            if e.errno == 9:
                print(
                    "Bad file descriptor error. This might be due to a network issue or the connection being closed unexpectedly.")
                return False
        except Exception as e:
            print(f"Other exception: {e}")
            return False
        finally:
            SSH_Client.close()
    @classmethod
    def delete_config(cls, server_id, config_uuid, inbound_id):
        server_obj = ServerModel.objects.get(server_id=server_id)
        url = server_obj.server_url + f"panel/api/inbounds/{inbound_id}/delClient/{config_uuid}"
        session = cls.create_session(server_id)
        if not session:
            return False
        respons = session.post(url)
        if respons.status_code == 200:
            if respons.json()['success']:
                session.close()
                return True
        return False

    @classmethod
    def disable_config(cls, session, server_id, config_uuid, inbound_id, config_name, enable, ip_limit, expire_time,
                       usage_limit):
        server_obj = ServerModel.objects.get(server_id=server_id)
        url = server_obj.server_url + f"panel/api/inbounds/updateClient/{config_uuid}"

        setting = {
            'clients': [{
                'id': str(config_uuid), 'alterId': 0, 'email': config_name,
                'limitIp': ip_limit, 'totalGB': usage_limit,
                'expiryTime': expire_time, 'enable': not enable,
                "tgId": '', 'subId': ''
            }]
        }
        data1 = {
            "id": int(inbound_id),
            "settings": json.dumps(setting)
        }
        header = {"Accept": "application/json"}
        try:
            respons = session.post(url, headers=header, json=data1)
            if respons.status_code == 200:
                if respons.json()['success']:
                    return True
            return False
        except Exception as e:
            return False

    @classmethod
    def create_test_config(cls, chat_id):
        with open(settings.BASE_DIR / "test_server.json", "r") as f:
            data = json.load(f)
            server_obj = ServerModel.objects.get(server_id=data["server_id"])
            inbound_id = data["inbound_id"]
            inbound_port = data["inbound_port"]
            url = server_obj.server_url + "panel/api/inbounds/addClient"
            expire_time = 24 * 60 * 60 * 1000 * -1
            usage_limit = int(convert_units(400, BinaryUnits.MB, BinaryUnits.BYTE)[0])
            config_uuid = str(uuid.uuid4())
            config_name = Configs.generate_unique_name() + "_Test"
            setting = {
                'clients': [{
                    'id': config_uuid, 'alterId': 0, 'email': config_name,
                    'limitIp': 0, 'totalGB': usage_limit,
                    'expiryTime': expire_time, 'enable': True,
                    "tgId": '', 'subId': ''
                }]
            }
            data1 = {
                "id": inbound_id,
                "settings": json.dumps(setting)
            }
            header = {"Accept": "application/json"}
            try:
                session = cls.create_session(server_obj.server_id)
                if not session:
                    return False
                respons = session.post(url, headers=header, json=data1, timeout=6)
                if respons.status_code == 200:
                    if respons.json()['success']:
                        session.close()
                        vless = ('📡 کانفیگ شما:' '\n\n'
                                 f"```\nvless://{config_uuid}@{server_obj.server_fake_domain}:{inbound_port}?"
                                 f"security=none&encryption=none&host=speedtest.net&headerType=http&type=tcp#{config_name}\n```"
                                 '\n' '💠 برای کپی کردن کانفیگ روی دکمه <<کپی کردن کد>> (Copy Code) کلیک کنید.' "\n\n" "❇️ حجم کانفیگ 400MB و مدت آن 1 روز میباشد.")
                        TestConfig.objects.create(customer=CustomerModel.objects.get(userid=chat_id), config_uuid=config_uuid, config_name=config_name).save()
                        return vless
                session.close()
                return False
            except Exception as e:
                return False


class Configs:
    @classmethod
    def save_config_info(cls, config_name, config_uuid, server_id, chat_id, price, paid=True, created_by='Bot'):
        if chat_id:
            chat_id = CustomerModel.objects.get(userid=chat_id)
        else:
            chat_id = None
        ConfigsInfo.objects.create(
            config_name=config_name,
            config_uuid=config_uuid,
            server=ServerModel.objects.get(server_id=server_id),
            chat_id=chat_id,
            created_by=created_by,
            paid=paid,
            price=price
        ).save()

    @classmethod
    def change_config_info(cls, config_uuid, price, paid):
        if ConfigsInfo.objects.filter(config_uuid=config_uuid).exists():
            config_info = ConfigsInfo.objects.get(config_uuid=config_uuid)
            config_info.renew_count += 1
            config_info.price = price
            config_info.paid = paid
            config_info.save()

    @classmethod
    def create_vless_text(cls, config_uuid, server_obj, config_name):
        vless = ('📡 کانفیگ شما:' '\n\n'
                 f"```\nvless://{config_uuid}@{server_obj.server_fake_domain}:{server_obj.inbound_port}?"
                 f"security=none&encryption=none&host=speedtest.net&headerType=http&type=tcp#{config_name}\n```"
                 '\n' '💠 برای کپی کردن کانفیگ روی دکمه <<کپی کردن کد>> (Copy Code) کلیک کنید.'
                 )
        return vless

    @classmethod
    def send_config_to_user(cls, user_id, config_uuid, server, config_name):
        from connection.command_runer import CommandRunner
        server_obj = ServerModel.objects.get(server_id=server)
        vless = cls.create_vless_text(config_uuid, server_obj, config_name)
        CommandRunner.send_msg_to_user(user_id, vless, keyboard=[{'text': 'دریافت QRcode', 'callback_data': f'QRcode<~>{config_uuid}'}])

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
            price=price,
        ).save()

    @classmethod
    def add_configs_to__tamdid__queue_before_confirm(cls, config_uuid, usage_limit, expire_time, user_limit, price):
        config_info = ConfigsInfo.objects.get(config_uuid=config_uuid)
        if TamdidConfigQueue.objects.filter(config=config_info, pay_status=0).exists():
            TamdidConfigQueue.objects.get(config=config_info, pay_status=0).delete()

        TamdidConfigQueue.objects.create(
            config=config_info,
            usage_limit=usage_limit,
            expire_time=expire_time,
            user_limit=user_limit,
            price=price
        ).save()

    @staticmethod
    def generate_unique_name():
        with open("settings.json", "r+") as f:
            setting = json.load(f)
            counter = setting["config_name_counter"]
            setting["config_name_counter"] += 1
            f.seek(0)
            json.dump(setting, f)
            f.truncate()
        # characters = string.ascii_uppercase
        # unique_char = ''.join(random.choice(characters) for _ in range(2))

        return 'NapsV_' + str(counter)

    @classmethod
    def set_unlimit_limit(cls, config_uuid, iplimit, month):
        with open(settings.BASE_DIR / "settings.json", "r") as f:
            data = json.load(f)["unlimit_limit"]
        if (month in [1, 2, 3]) and (iplimit in [1, 2]):
            limit = data[f"{iplimit}u"][f"{month}m"]
        else:
            iplimit = max(1, min(iplimit, 2))
            month = max(1, min(month, 3))
            limit = data[f"{iplimit}u"][f"{month}m"]
        if InfinitCongisLimit.objects.filter(config__config_uuid=config_uuid).exists():
            obj = InfinitCongisLimit.objects.get(config__config_uuid=config_uuid)
            obj.limit = limit
            obj.save()
        else:
            InfinitCongisLimit.objects.create(config=ConfigsInfo.objects.get(config_uuid=config_uuid), limit=limit).save()

    @classmethod
    def create_config_from_queue(cls, config_uuid, by_celery=False):
        from connection.command_runer import CommandRunner
        config_queue_obj = CreateConfigQueue.objects.get(config_uuid=config_uuid)
        config_queue_obj.sent_to_user = 1
        config_queue_obj.save()
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
            if UserActiveOffCodes.objects.filter(custumer=config_queue_obj.custumer, used=False).exists():
                off_obj = UserActiveOffCodes.objects.get(custumer=config_queue_obj.custumer, used=False)
                off_obj.used = True
                off_obj.save()
            change_wallet_amount(config_queue_obj.custumer.userid, -1 * config_queue_obj.price)
            config_queue_obj.sent_to_user = 3
            cls.save_config_info(config_queue_obj.config_name, config_queue_obj.config_uuid,
                                 config_queue_obj.server.server_id, config_queue_obj.custumer.userid,
                                 config_queue_obj.price)

            cls.send_config_to_user(config_queue_obj.custumer.userid, config_uuid,config_queue_obj.server.server_id, config_queue_obj.config_name)
            if config_queue_obj.usage_limit == 0:
                cls.set_unlimit_limit(config_uuid, config_queue_obj.user_limit, int(config_queue_obj.expire_time / 30))
                CommandRunner.send_infinit_notification(config_queue_obj.custumer.userid, config_queue_obj.user_limit, int(config_queue_obj.expire_time / 30))

            Log.create_config_log(ConfigsInfo.objects.get(config_uuid=config_uuid),
                                  f"➕ Create by \"Bot\" ({config_queue_obj.usage_limit}GB - {config_queue_obj.expire_time}day - {config_queue_obj.user_limit}Ip - {int(config_queue_obj.price / 1000)}T)")
            Log.create_admin_log("Bot",
                                 f"➕ Create \"{config_queue_obj.config_name}\" ({config_queue_obj.usage_limit}GB - {config_queue_obj.expire_time}day - {config_queue_obj.user_limit}Ip - {int(config_queue_obj.price / 1000)}T)")
            Log.create_customer_log(CustomerModel.objects.get(userid=config_queue_obj.custumer.userid),
                                    f"➕ Create \"{config_queue_obj.config_name}\" by \"Bot\" ({config_queue_obj.usage_limit}GB - {config_queue_obj.expire_time}day - {config_queue_obj.user_limit}Ip - {int(config_queue_obj.price / 1000)}T)")
        else:
            config_queue_obj.sent_to_user = 5
            config_queue_obj.save()
            if not by_celery:
                CommandRunner.send_msg_to_user(config_queue_obj.custumer.userid,'🟢 کابر گرامی کانفیگ شما تا دقایقی دیگر به صورت خودکار برای شما ارسال میشود.')

    @classmethod
    def create_config_from_wallet(cls, chat_id, server_id, expire_limit, usage_limit, user_limit, price):
        from connection.command_runer import CommandRunner
        server_obj = ServerModel.objects.get(server_id=server_id)
        conf_uuid = str(uuid.uuid4())
        config_name = Configs.generate_unique_name()
        create_config = ServerApi.create_config(server_id, config_name, conf_uuid, usage_limit, expire_limit * 30,
                                                user_limit, True)
        if create_config:
            if UserActiveOffCodes.objects.filter(custumer__userid=chat_id, used=False).exists():
                off_obj = UserActiveOffCodes.objects.get(custumer__userid=chat_id, used=False)
                off_obj.used = True
                off_obj.save()
            cls.save_config_info(config_name, conf_uuid, server_id, chat_id, price)
            change_wallet_amount(chat_id, -1 * price)
            cls.send_config_to_user(chat_id, conf_uuid, server_id, config_name)
            if usage_limit == 0:
                cls.set_unlimit_limit(conf_uuid, user_limit, expire_limit)
                CommandRunner.send_infinit_notification(chat_id, user_limit, expire_limit)

            Log.create_config_log(ConfigsInfo.objects.get(config_uuid=conf_uuid),
                                  f"➕ Create by \"Bot\" ({usage_limit}GB - {expire_limit}day - {user_limit}Ip - {int(price / 1000)}T)")
            Log.create_admin_log("Bot",
                                 f"➕ Create \"{config_name}\" ({usage_limit}GB - {expire_limit}day - {user_limit}Ip - {price}T)")
            Log.create_customer_log(CustomerModel.objects.get(userid=chat_id),
                                    f"➕ Create \"{config_name}\" by \"Bot\" ({usage_limit}GB - {expire_limit}day - {user_limit}Ip - {int(price / 1000)}T)")
            return True
        return False

    @classmethod
    def create_config_by_admins(cls, server_id, expire_limit, usage_limit, user_limit, price, paid, created_by):
        conf_uuid = uuid.uuid4()
        config_name = Configs.generate_unique_name()
        create_config = ServerApi.create_config(server_id, config_name, conf_uuid, usage_limit, expire_limit,
                                                user_limit, True)
        if create_config:
            cls.save_config_info(config_name, conf_uuid, server_id, None, price, paid, created_by)
            if usage_limit == 0:
                cls.set_unlimit_limit(conf_uuid, user_limit, int(expire_limit / 30))
            Log.create_config_log(ConfigsInfo.objects.get(config_uuid=conf_uuid),
                                  f"➕ Create by \"{created_by}\" ({usage_limit}GB - {expire_limit}day - {user_limit}Ip - {int(price / 1000)}T)")
            Log.create_admin_log(created_by,
                                 f"➕ Create \"{config_name}\" ({usage_limit}GB - {expire_limit}day - {user_limit}Ip - {int(price / 1000)}T)")

            return {'config_name': config_name, 'config_uuid': conf_uuid}
        return None


    @classmethod
    def tamdid_config_from_queue(cls, config_uuid, by_celery=False):
        from connection.command_runer import CommandRunner
        config_queue_obj = TamdidConfigQueue.objects.get(config__config_uuid=config_uuid, sent_to_user=0)
        config_queue_obj.sent_to_user = 1
        config_queue_obj.save()
        respons = ServerApi.renew_config(
            server_id=config_queue_obj.config.server.server_id,
            config_name=config_queue_obj.config.config_name,
            config_uuid=config_uuid,
            total_usage=config_queue_obj.usage_limit,
            expire_time=config_queue_obj.expire_time,
            ip_limit=config_queue_obj.user_limit,
        )
        if respons:
            if UserActiveOffCodes.objects.filter(custumer__userid=config_queue_obj.config.chat_id.userid, used=False).exists():
                off_obj = UserActiveOffCodes.objects.get(custumer__userid=config_queue_obj.config.chat_id.userid, used=False)
                off_obj.used = True
                off_obj.save()
            change_wallet_amount(config_queue_obj.config.chat_id.userid, -1 * config_queue_obj.price)
            config_queue_obj.sent_to_user = 3
            cls.change_config_info(config_queue_obj.config.config_uuid, config_queue_obj.price, True)
            if config_queue_obj.usage_limit == 0:
                cls.set_unlimit_limit(config_uuid, config_queue_obj.user_limit, int(config_queue_obj.expire_time / 30))
                CommandRunner.send_infinit_notification(config_queue_obj.config.chat_id.userid, config_queue_obj.user_limit, int(config_queue_obj.expire_time / 30))
            CommandRunner.send_msg_to_user(config_queue_obj.config.chat_id.userid,
                                           f"✅ سرویس {config_queue_obj.config.config_name} تمدید شد. از بخش (سرویس های من) در منوی اصلی میتوانید وضعیت سرویس خود را مشاهده کنید.")

            Log.create_config_log(config_queue_obj.config,
                                  f"🔃 Renew by \"Bot\" ({config_queue_obj.usage_limit}GB - {config_queue_obj.expire_time}day - {config_queue_obj.user_limit}Ip - {int(config_queue_obj.price / 1000)}T)")
            Log.create_admin_log("Bot",
                                 f"🔃 Renew \"{config_queue_obj.config.config_name}\" ({config_queue_obj.usage_limit}GB - {config_queue_obj.expire_time}day - {config_queue_obj.user_limit}Ip - {int(config_queue_obj.price / 1000)}T)")
            Log.create_customer_log(config_queue_obj.config.chat_id,
                                    f"🔃 Renew \"{config_queue_obj.config.config_name}\" by \"Bot\" ({config_queue_obj.usage_limit}GB - {config_queue_obj.expire_time}day - {config_queue_obj.user_limit}Ip - {int(config_queue_obj.price / 1000)}T)")
        else:
            config_queue_obj.sent_to_user = 5
            config_queue_obj.save()
            if not by_celery:
                CommandRunner.send_msg_to_user(config_queue_obj.config.chat_id.userid,
                                               '🟢 کابر گرامی کانفیگ شما تا دقایقی دیگر به صورت خودکار تمدید میشود.')

    @classmethod
    def tamdid_config_from_wallet(cls, config_uuid, expire_limit, usage_limit, user_limit, price):
        from connection.command_runer import CommandRunner
        config_obj = ConfigsInfo.objects.get(config_uuid=config_uuid)
        renew_config = ServerApi.renew_config(config_obj.server.server_id, config_uuid, config_obj.config_name,
                                              expire_limit * 30, usage_limit, user_limit)
        if renew_config:
            if UserActiveOffCodes.objects.filter(custumer__userid=config_obj.chat_id.userid, used=False).exists():
                off_obj = UserActiveOffCodes.objects.get(custumer__userid=config_obj.chat_id.userid, used=False)
                off_obj.used = True
                off_obj.save()
            cls.change_config_info(config_uuid, price, True)
            change_wallet_amount(config_obj.chat_id.userid, -1 * price)

            if usage_limit == 0:
                cls.set_unlimit_limit(config_uuid, user_limit, expire_limit)
                CommandRunner.send_infinit_notification(config_obj.chat_id.userid, user_limit, expire_limit)

            CommandRunner.send_msg_to_user(config_obj.chat_id.userid,f"✅ سرویس {config_obj.config_name} تمدید شد. از بخش (سرویس های من) در منوی اصلی میتوانید وضعیت سرویس خود را مشاهده کنید.")
            Log.create_config_log(config_obj,f"🔃 Renew by \"Bot\" ({usage_limit}GB - {expire_limit}day - {user_limit}Ip - {int(price / 1000)}T)")
            Log.create_admin_log("Bot",f"🔃 Renew \"{config_obj.config_name}\" ({usage_limit}GB - {expire_limit}day - {user_limit}Ip - {int(price / 1000)}T)")
            Log.create_customer_log(config_obj.chat_id,f"🔃 Renew \"{config_obj.config_name}\" by \"Bot\" ({usage_limit}GB - {expire_limit}day - {user_limit}Ip - {int(price / 1000)}T)")

            config_obj.renew_count += 1
            config_obj.price = True
            config_obj.save()
            return True
        return False

    @classmethod
    def tamdid_config_by_admins(cls, config_uuid, expire_limit, usage_limit, user_limit, price, paid, by_admin):
        from connection.command_runer import CommandRunner

        conf = ConfigsInfo.objects.get(config_uuid=config_uuid)
        create_config = ServerApi.renew_config(conf.server.server_id, config_uuid, conf.config_name, expire_limit,
                                               usage_limit, user_limit)

        if create_config:
            cls.change_config_info(config_uuid, price, paid)
            if usage_limit == 0:
                cls.set_unlimit_limit(config_uuid, user_limit, int(expire_limit / 30))

            Log.create_config_log(conf,f"🔃 Renew \"{conf.config_name}\" by \"{by_admin}\" ({usage_limit}GB - {expire_limit}day - {user_limit}Ip - {int(price / 1000)}T)")
            Log.create_admin_log(by_admin,f"🔃 Renew \"{conf.config_name}\" ({usage_limit}GB - {expire_limit}day - {user_limit}Ip - {int(price / 1000)}T)")
            if conf.chat_id:
                CommandRunner.send_msg_to_user(conf.chat_id.userid,
                                               f" ✅ سرویس {conf.config_name} توسط ادمین تمدید شد. از بخش (سرویس های من) در منوی اصلی میتوانید وضعیت سرویس خود را مشاهده کنید. ")
                Log.create_customer_log(conf.chat_id,f"🔃 Renew \"{conf.config_name}\" by \"{by_admin}\" ({usage_limit}GB - {expire_limit}day - {user_limit}Ip - {int(price / 1000)}T)")
                if usage_limit == 0:
                    CommandRunner.send_infinit_notification(conf.chat_id.userid, user_limit, int(expire_limit / 30))

            return {'config_name': conf.config_name, 'config_uuid': config_uuid}
        return None


class ListConfigs(LoginRequiredMixin, View):
    def get(self, request, server_id, *args, **kwargs):
        data = ServerApi.get_list_configs(server_id)
        if not data:
            messages.error(request,
                           f"اتصال به سرور {ServerModel.objects.get(server_id=server_id).server_name} برقرار نشد.")
        searchform = SearchForm()
        return render(request, "list_configs.html", {"data": data, 'searchform': searchform, 'server_id': server_id})

    def post(self, request, server_id, *args, **kwargs):
        data = ServerApi.get_list_configs(server_id)
        searchform = SearchForm(request.POST)
        if not data:
            messages.error(request,
                           f"اتصال به سرور {ServerModel.objects.get(server_id=server_id).server_name} برقرار نشد.")
            return render(request, "list_configs.html",
                          {"data": data, 'searchform': searchform, "searched": True, 'server_id': server_id})
        if searchform.is_valid():
            word = searchform.cleaned_data["search"]
            for conf in list(data):
                if (not word.lower() in conf.lower()) and (not word.lower() in data[conf]["uuid"].lower()):
                    del data[conf]
            return render(request, "list_configs.html",
                          {"data": data, "searchform": searchform, "searched": True, 'server_id': server_id})


class ListConfigsSearched(LoginRequiredMixin, View):
    def post(self, request):
        form = SearchConfigForm(request.POST)
        if form.is_valid():
            word = form.cleaned_data["search_config"]
            model_obj = ConfigsInfo.objects.filter(Q(config_name__icontains=word) | Q(config_uuid__icontains=word))
            if not model_obj.exists():
                messages.error(request, 'کانفیگی با این مشخصات یافت نشد.')
            return render(request, "list_configs_searched.html",
                          {"configs_model": reversed(model_obj), "search_config": form})
        return redirect('accounts:home')


class ConfigPage(LoginRequiredMixin, View):
    def get(self, request, server_id, config_uuid, config_name):
        if ConfigsInfo.objects.filter(config_uuid=config_uuid).exists():
            config_info = ConfigsInfo.objects.get(config_uuid=config_uuid)
            conf_log = reversed(ConfigLog.objects.filter(config=config_info))
        else:
            conf_log = None
            config_info = False
        config_usage = ServerApi.get_list_configs(server_id)
        if config_usage:
            if config_name in config_usage:
                config_usage = config_usage[config_name]
                get_config_link = f"نام سرویس: {config_name}" "\n\n" "برای دریافت کانفیگ روی لینک زیر کلیک کنید 👇🏻" "\n"  f'tg://resolve?domain={BOT_USERNAME}&start=register_{config_uuid}'
                vless = Configs.create_vless_text(config_uuid, ServerModel.objects.get(server_id=server_id),
                                                  config_name)
                return render(request, 'config_page.html', {'config_info': config_info, 'vless': vless,
                                                            'config_usage': config_usage, 'config_name': config_name,
                                                            "get_config_link": get_config_link, "server_id": server_id,
                                                            "conf_log": conf_log})
            messages.error(request, "کانفیگ حذف شده است.")
            return redirect(request.META.get('HTTP_REFERER', '/'))
        messages.error(request, "کانفیگ در دیتابیس پیدا نشد یا اتصال به سرور برقرار نشد.")
        return redirect(request.META.get('HTTP_REFERER', '/'))


class CreateConfigPage(LoginRequiredMixin, View):
    def get(self, request, server_id, form_type):
        forms = {'auto': CreateConfigForm, 'manual': ManualCreateConfigForm}
        return render(request, 'create_config.html',
                      {'server': ServerModel.objects.get(server_id=server_id), 'form': forms[form_type],
                       'form_type': form_type})

    def post(self, request, server_id, form_type):
        forms = {'auto': CreateConfigForm, 'manual': ManualCreateConfigForm}
        form = forms[form_type](request.POST)
        if form.is_valid():
            ip_limit = 0
            time_limit = 0
            usage = 0
            cd = form.cleaned_data

            if cd['type'] == "limited":
                usage = int(cd["usage_limit"])
                time_limit = int(cd['days_limit'])
            elif cd['type'] == 'usage_unlimit':
                time_limit = int(cd['days_limit'])
                ip_limit = int(cd['ip_limit'])
            elif cd['type'] == 'time_unlimit':
                usage = int(cd["usage_limit"])

            if form_type == 'auto':
                price = PricesModel.objects.get(usage_limit=usage, expire_limit=time_limit, user_limit=ip_limit).price
            else:
                price = cd['price']
            paid = cd["paid"]
            if form_type == 'auto':
                time_limit = time_limit * 30
            create_config = Configs.create_config_by_admins(server_id, time_limit, usage, ip_limit, price, paid,
                                                            request.user.username),

            if create_config[0]:
                return redirect('servers:conf_page', server_id, create_config[0]["config_uuid"],
                                create_config[0]["config_name"])

            messages.error(request, "اتصال به سرور برقرار نشد.")

        return render(request, 'create_config.html',
                      {'server': ServerModel.objects.get(server_id=server_id), 'form': form, 'form_type': form_type})


class ApiGetConfigTimeChoices(APIView):
    def get(self, request):
        sleep(0.25)
        type = request.GET.get('type')
        choices = []
        if type == 'limited':
            obj = PricesModel.objects.filter(~Q(usage_limit=0) & ~Q(expire_limit=0))
            for i in obj:
                if not (i.expire_limit, f"{i.expire_limit} ماه") in choices:
                    choices.append((i.expire_limit, f"{i.expire_limit} ماه"))
        elif type == 'usage_unlimit':
            obj = PricesModel.objects.filter(Q(usage_limit=0) & ~Q(expire_limit=0))
            for i in obj:
                if not (i.expire_limit, f"{i.expire_limit} ماه") in choices:
                    choices.append((i.expire_limit, f"{i.expire_limit} ماه"))
        elif type == 'time_unlimit':
            choices.append((0, '∞'))

        choices = sorted(choices, key=lambda x: x[0])
        return Response({'choices': choices})


class ApiGetConfigUsageChoices(APIView):
    def get(self, request):
        type = request.GET.get('type')
        time = int(request.GET.get('time'))
        choices = []
        if type == 'limited':
            time = time
            obj = PricesModel.objects.filter(~Q(usage_limit=0) & Q(expire_limit=time))
            for i in obj:
                if not (i.usage_limit, f"{i.usage_limit} GB") in choices:
                    choices.append((i.usage_limit, f"{i.usage_limit} GB"))

        elif type == 'usage_unlimit':
            choices.append((0, '∞'))

        elif type == 'time_unlimit':
            obj = PricesModel.objects.filter(~Q(usage_limit=0) & Q(expire_limit=0))
            for i in obj:
                if not (i.usage_limit, f"{i.usage_limit} GB") in choices:
                    choices.append((i.usage_limit, f"{i.usage_limit} GB"))

        choices = sorted(choices, key=lambda x: x[0])
        return Response({'choices': choices})


class ApiGetConfigIPLimitChoices(APIView):
    def get(self, request):
        type = request.GET.get('type')
        time = int(request.GET.get('time'))

        choices = []
        if type == 'limited' or type == 'time_unlimit':
            choices.append((0, '∞'))

        elif type == 'usage_unlimit':
            time = time
            obj = PricesModel.objects.filter(Q(usage_limit=0) & Q(expire_limit=time))
            for i in obj:
                if not (i.user_limit, f"{i.user_limit} کاربره") in choices:
                    choices.append((i.user_limit, f"{i.user_limit} کاربره"))

        choices = sorted(choices, key=lambda x: x[0])
        return Response({'choices': choices})


class ApiGetConfigPriceChoices(APIView):
    def get(self, request):
        time = int(request.GET.get('time'))
        iplimit = int(request.GET.get('iplimit'))
        usage = int(request.GET.get('usage'))
        obj = PricesModel.objects.get(usage_limit=usage, expire_limit=time, user_limit=iplimit).price
        return Response({'price': f'{obj:,}'})


class DeleteConfig(LoginRequiredMixin, View):
    def get(self, request, server_id, config_uuid, config_name, inbound_id):
        delete = ServerApi.delete_config(server_id, config_uuid, inbound_id)
        if delete:
            messages.success(request, f"کانفیگ {config_name} با موفقیت حذف شد.")
            if ConfigsInfo.objects.filter(config_uuid=config_uuid).exists():
                obj = ConfigsInfo.objects.get(config_uuid=config_uuid)

                if obj.chat_id:
                    Log.create_customer_log(obj.chat_id, f"❌ Delete \"{config_name}\" by \"{request.user.username}\"")
                obj.delete()
            Log.create_admin_log(f"{request.user.username}", f"❌ Delete \"{config_name}\"")


        else:
            messages.error(request, "ارور در حذف کانفیگ")
        return redirect('servers:list_configs', server_id)


class DisableConfig(LoginRequiredMixin, View):
    def get(self, request, server_id, config_uuid, inbound_id, config_name, enable, ip_limit):
        server_obj = ServerModel.objects.get(server_id=server_id)
        url = server_obj.server_url + f"panel/api/inbounds/getClientTraffics/{config_name}"
        session = ServerApi.create_session(server_id)
        if not session:
            return False
        respons = session.get(url)
        if respons.status_code == 200:
            if respons.json()['success']:
                obj = respons.json()["obj"]
                if obj:
                    ServerApi.disable_config(session, server_id, config_uuid, inbound_id, config_name, bool(enable),
                                             ip_limit, obj['expiryTime'], obj['total'])
                    messages.success(request, f"کانفیگ {config_name} با موفقیت فعال/غیرفعال شد.")
                    action = "⛔ Disable" if enable == 1 else "✅ Enable"
                    Log.create_admin_log(f"{request.user.username}", f"{action} \"{config_name}\"")
                    if ConfigsInfo.objects.filter(config_uuid=config_uuid).exists():
                        Log.create_config_log(ConfigsInfo.objects.get(config_uuid=config_uuid),
                                              f"{action} by \"{request.user.username}\" ")
                        if ConfigsInfo.objects.get(config_uuid=config_uuid).chat_id:
                            Log.create_customer_log(ConfigsInfo.objects.get(config_uuid=config_uuid).chat_id,
                                                    f"{action} \"{config_name}\" by \"{request.user.username}\" ")
            else:
                messages.error(request, f"ارور در اتصال یه سرور.")
        else:
            messages.error(request, f"ارور در اتصال یه سرور.")
        return redirect(request.META.get('HTTP_REFERER', '/'))
        # return redirect('servers:list_configs', server_id)


class ShowServers(LoginRequiredMixin, View):
    def get(self, request):
        obj = ServerModel.objects.all()
        return render(request, "show_servers.html", {'servers': obj})


class AddServer(LoginRequiredMixin, View):
    def get(self, request):
        form = AddServerForm()
        return render(request, "add_server.html", {'form': form})

    def post(self, request):
        form = AddServerForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            ServerModel.objects.create(
                server_id=cd["server_id"],
                server_name=cd["server_name"],
                server_url=cd["server_url"],
                username=cd["username"],
                password=cd["password"],
                server_fake_domain=cd["server_fake_domain"],
                inbound_id=cd["inbound_id"],
                inbound_port=cd["inbound_port"],
                active=cd["active"],
                iphone=cd["iphone"]
            ).save()
            return redirect('servers:show_servers')
        return render(request, "add_server.html", {'form': form})


class EditServer(LoginRequiredMixin, View):
    def get(self, request, server_id):
        form = EditServerForm(server_id=server_id)
        return render(request, "add_server.html", {'form': form})

    def post(self, request, server_id):
        form = EditServerForm(request.POST, server_id=server_id)
        if form.is_valid():
            cd = form.cleaned_data
            obj = ServerModel.objects.get(server_id=server_id)
            obj.server_name = cd["server_name"]
            obj.server_url = cd["server_url"]
            obj.username = cd["username"]
            obj.password = cd["password"]
            obj.server_fake_domain = cd["server_fake_domain"]
            obj.inbound_id = cd["inbound_id"]
            obj.inbound_port = cd["inbound_port"]
            obj.active = cd["active"]
            obj.iphone = cd["iphone"]
            obj.save()
            return redirect('servers:show_servers')
        return render(request, "add_server.html", {'form': form, "edit": True})


class RenewPage(LoginRequiredMixin, View):

    def get(self, request, uuid, form_type):
        conf = ConfigsInfo.objects.get(config_uuid=uuid)
        forms = {'auto': CreateConfigForm, 'manual': ManualCreateConfigForm}
        return render(request, 'renew_config.html',
                      {"config": conf, 'form': forms[form_type], 'form_type': form_type})

    def post(self, request, uuid, form_type):
        conf = ConfigsInfo.objects.get(config_uuid=uuid)
        forms = {'auto': CreateConfigForm, 'manual': ManualCreateConfigForm}
        form = forms[form_type](request.POST)
        if form.is_valid():
            ip_limit = 0
            time_limit = 0
            usage = 0
            cd = form.cleaned_data
            if cd['type'] == "limited":
                usage = int(cd["usage_limit"])
                time_limit = int(cd['days_limit'])
            elif cd['type'] == 'usage_unlimit':
                time_limit = int(cd['days_limit'])
                ip_limit = int(cd['ip_limit'])
            elif cd['type'] == 'time_unlimit':
                usage = int(cd["usage_limit"])
            if form_type == 'auto':
                price = PricesModel.objects.get(usage_limit=usage, expire_limit=time_limit,
                                                user_limit=ip_limit).price
            else:
                price = cd['price']
            paid = cd["paid"]
            if form_type == "auto":
                time_limit *= 30
            create_config = Configs.tamdid_config_by_admins(uuid, time_limit, usage, ip_limit, price, paid,
                                                            request.user.username)
            if create_config:
                messages.success(request, f"سرویس {conf.config_name} با موفقیت تمدید شد.")
                return redirect('servers:conf_page', conf.server.server_id, create_config["config_uuid"],
                                create_config["config_name"])
            messages.error(request, "اتصال به سرور برقرار نشد.")
        return render(request, 'renew_config.html', {"config": conf, 'form': forms[form_type], 'form_type': form_type})


class ChangeConfigPage(LoginRequiredMixin, View):
    def get(self, request, config_uuid, config_name, server_id):
        api = ServerApi.get_list_configs(server_id)[config_name]
        form = ChangeConfigSettingForm(
            config_data={"usage": api["usage_limit"], "expire_time": api["expire_time"], "ip_limit": api["ip_limit"]})
        return render(request, "change_config.html",
                      {"config": api, "form": form, 'server_id': server_id, 'config_name': config_name})

    def post(self, request, config_uuid, config_name, server_id):
        form = ChangeConfigSettingForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            usage_limit = cd["usage_limit"]
            days_limit = cd["days_limit"]
            ip_limit = cd["ip_limit"]
            post = ServerApi.renew_config(server_id, config_uuid, config_name, days_limit, usage_limit, ip_limit,
                                          reset=False)
            if post:
                messages.success(request, "کانفیگ با موفقیت آپدیت شد.")

                Log.create_admin_log(f"{request.user.username}",
                                     f"⚙️ Edit \"{config_name}\" ({usage_limit}GB - {days_limit}day - {ip_limit}Ip)")
                if ConfigsInfo.objects.filter(config_uuid=config_uuid):
                    Log.create_config_log(ConfigsInfo.objects.get(config_uuid=config_uuid),
                                          f"⚙️ Edit by \"{request.user.username}\" ({usage_limit}GB - {days_limit}day - {ip_limit}Ip)")
                    if cus := ConfigsInfo.objects.get(config_uuid=config_uuid).chat_id:
                        Log.create_customer_log(cus,
                                                f"⚙️ Edit \"{config_name}\" by \"{request.user.username}\" ({usage_limit}GB - {days_limit}day - {ip_limit}Ip)")

                return redirect("servers:conf_page", server_id, config_uuid, config_name)
            else:
                messages.error(request, "ارور در اتصال به سرور.")
        api = ServerApi.get_list_configs(server_id)[config_name]
        form = ChangeConfigSettingForm(request.POST,
                                       config_data={"usage": api["usage_limit"], "expire_time": api["expire_time"],
                                                    "ip_limit": api["ip_limit"]})
        return render(request, "change_config.html",
                      {"config": api, "form": form, 'server_id': server_id, 'config_name': config_name})


class ChangeConfigLocationPage(LoginRequiredMixin, View):
    def get(self, request, config_uuid, server_id):
        config = ConfigsInfo.objects.get(config_uuid=config_uuid)
        form = ChangeConfigLocForm(server=server_id)
        return render(request, "change_conf_location.html", {"form": form, 'server_id': server_id, "config": config})

    def post(self, request, config_uuid, server_id):
        config = ConfigsInfo.objects.get(config_uuid=config_uuid)
        form = ChangeConfigLocForm(request.POST)
        from_server = config.server.server_name
        if form.is_valid():
            cd = form.cleaned_data
            change = ServerApi.change_location(server_id, cd["server"], config_uuid)
            if change:
                config.server = ServerModel.objects.get(server_id=cd["server"])
                config.save()
                Log.create_config_log(config,
                                      f"🌎 Change Location by \"{request.user.username}\" from \"{from_server}\" to \"{ServerModel.objects.get(server_id=cd["server"]).server_name}\"")
                Log.create_admin_log(f"{request.user.username}",
                                     f"🌎 Change Location \"{config.config_name}\" from \"{from_server}\" to \"{ServerModel.objects.get(server_id=cd["server"]).server_name}\"")
                if config.chat_id:
                    Log.create_customer_log(config.chat_id,
                                            f"🌎 Change Location \"{config.config_name}\" by \"{request.user.username}\" from \"{from_server}\" to \"{ServerModel.objects.get(server_id=cd["server"]).server_name}\"")

            return redirect("servers:conf_page", cd["server"], config_uuid, config.config_name)
        return render(request, "change_conf_location.html", {"form": form, 'server_id': server_id, "config": config})


class ChangeUnlimitConfLimit(LoginRequiredMixin, View):
    def get(self, request, config_uuid):
        config = ConfigsInfo.objects.get(config_uuid=config_uuid)
        if InfinitCongisLimit.objects.filter(config=config).exists():
            limit = InfinitCongisLimit.objects.get(config=config).limit
        else:
            limit = False
        form = ChangeUnlimitConfLimitForm(limit=limit)
        return render(request, "change_unlimit_limit.html", {"form": form, 'config': config})

    def post(self, request, config_uuid):
        config = ConfigsInfo.objects.get(config_uuid=config_uuid)
        if InfinitCongisLimit.objects.filter(config=config).exists():
            limit = InfinitCongisLimit.objects.get(config=config).limit
        else:
            limit = False
        form = ChangeUnlimitConfLimitForm(request.POST, limit=limit)
        if form.is_valid():
            limit = form.cleaned_data["limit"]
            if InfinitCongisLimit.objects.filter(config=config).exists():
                limit_obj = InfinitCongisLimit.objects.get(config=config)
                limit_obj.limit = limit
                limit_obj.save()
            else:
                InfinitCongisLimit.objects.create(config=config, limit=limit).save()
            return redirect("servers:conf_page",config.server.server_id ,config_uuid, config.config_name)

        return render(request, "change_unlimit_limit.html", {"form": form, 'config': config})