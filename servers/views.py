import uuid
from binary import BinaryUnits, convert_units
from django.shortcuts import render
from .models import Server as ServerModel
import requests
from django.conf import settings
import json
from servers.models import CreateConfigQueue
import random
import string
from custumers.models import Customer as CustomerModel
class ServerApi:
    @classmethod
    def create_session(cls, server_id):
        server_obj = ServerModel.objects.get(server_id=server_id)
        print(server_obj)
        server_url = server_obj.server_url
        incound_id = server_obj.inbound_id
        login_payload = {"username": server_obj.username, "password": server_obj.password}
        login_url = server_url + "login/"
        header = {"Accept": "application/json"}
        session = requests.Session()
        login_response = session.post(login_url, headers=header, json=login_payload, timeout=15)
        if not login_response.json()["success"]:
            return False  # todo: redirect
        else:
            print("loged in")
            return session

    @classmethod
    def get_list_configs(cls, server_id):
        server_obj = ServerModel.objects.get(server_id=server_id)
        session = cls.create_session(server_id)
        list_configs = session.get(server_obj.server_url + "panel/api/inbounds/list/", timeout=15)
        joined_data = {}
        for respons in list_configs.json()["obj"]:
            for i in respons["clientStats"]:
                joined_data[i["email"]] = {
                    'enable':i["enable"],
                    'usage': i["up"] + i["down"],
                    'expire_time': i['expiryTime'],
                    'usage_limit': i['total'],
                    'inbound_id': i["inboundId"]
                }
            for i in json.loads(respons["settings"])["clients"]:
                joined_data[i["email"]]['uuid'] = i["id"]
                joined_data[i["email"]]['ip_limit'] = i["limitIp"]
        print(joined_data)
        return joined_data

    @classmethod
    def create_config(cls, server_id, config_name, usage_limit_GB, expire_DAY, ip_limit, enable):
        server_obj = ServerModel.objects.get(server_id=server_id)
        url = server_obj.server_url + "panel/api/inbounds/addClient"
        uid = uuid.uuid4()
        expire_time = str(int(expire_DAY) * 24 * 60 * 60 * 1000 * -1)
        usage_limit = str(int(convert_units(int(usage_limit_GB), BinaryUnits.GB, BinaryUnits.BYTE)[0]))
        setting = {
            'clients' : [{
                'id': str(uid), 'alterId': 0 , 'email': config_name,
                'limitIp' : ip_limit, 'totalGB': usage_limit,
                'expiryTime': expire_time , 'enable': enable ,
                "tgId":'', 'subId':''
            }]
        }
        data1 = {
            "id": int(server_obj.inbound_id),
            "settings": json.dumps(setting)
        }
        header = {"Accept": "application/json"}
        session = cls.create_session(server_id)
        respons = session.post(url, headers=header, json=data1)
        print(respons)
        return respons



class Configs:
    @classmethod
    def add_configs_to_queue_before_confirm(cls, server_id,user_id, config_uuid, usage_limit, expire_time, user_limit, price):
        user_obj = CustomerModel.objects.get(userid=user_id)
        if CreateConfigQueue.objects.filter(userid=user_obj, pay_confirm=False).exists():
            CreateConfigQueue.objects.get(userid=user_obj, pay_confirm=False).delete()

        CreateConfigQueue.objects.create(
            userid=user_obj,
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