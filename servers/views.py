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
from servers.models import CreateConfigQueue
import random
import string
from custumers.models import Customer as CustomerModel
from .forms import SearchForm, CreateConfigForm, ManualCreateConfigForm
from django.contrib import messages
from accounts.forms import SearchConfigForm
from finance.models import Prices as PricesModel
from rest_framework.views import APIView
from rest_framework.response import Response
from time import sleep, time
from os import environ

BOT_USERNAME = environ.get('BOT_USERNAME')

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
        try:
            server_obj = ServerModel.objects.get(server_id=server_id)
            session = cls.create_session(server_id)
            if not session:
                return False
            list_configs = session.get(server_obj.server_url + "panel/api/inbounds/list/", timeout=15)
            if list_configs.status_code != 200:
                return False
            joined_data = {}
            for respons in list_configs.json()["obj"]:
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
                    total_usage = int(convert_units(i['total'], BinaryUnits.BYTE, BinaryUnits.GB)[0])
                    joined_data[i["email"]] = {
                        'ended': i["enable"],
                        'usage': usage,
                        'started': started,
                        'expire_time': time_expire,
                        'usage_limit': total_usage,
                        'inbound_id': i["inboundId"]
                    }
                for i in json.loads(respons["settings"])["clients"]:
                    joined_data[i["email"]]['uuid'] = i["id"]
                    joined_data[i["email"]]['ip_limit'] = i["limitIp"]
                    joined_data[i["email"]]['enable'] = i["enable"]
            return joined_data
        except Exception as e:
            print(e)
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
                    return True
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
                    print(obj)
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
                    total_usage = int(convert_units(obj['total'], BinaryUnits.BYTE, BinaryUnits.GB)[0])
                    return {
                        'ended': obj["enable"],
                        'time_expire': time_expire,
                        'usage': usage,
                        'usage_limit': total_usage,
                        'started': started,
                        'exp_time_sta': expired,
                        'inbound_id': int(obj["inboundId"])
                    }

        return False

    @classmethod
    def delete_config(cls, server_id, config_uuid, inbound_id):
        server_obj = ServerModel.objects.get(server_id=server_id)
        url = server_obj.server_url + f"panel/api/inbounds/{inbound_id}/delClient/{config_uuid}"
        session = cls.create_session(server_id)
        if not session:
            return False
        respons = session.post(url)
        print(respons.json())
        if respons.status_code == 200:
            if respons.json()['success']:
                return True
        return False

    @classmethod
    def disable_config(cls,session ,server_id, config_uuid, inbound_id, config_name, enable, ip_limit, expire_time, usage_limit):
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
        CommandRunner.send_msg_to_user(user_id, vless)

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
        characters = string.ascii_uppercase
        numbers = string.digits
        unique_char = ''.join(random.choice(characters) for _ in range(2))
        unique_number = ''.join(random.choice(numbers) for _ in range(4))
        return 'NapsV_' + unique_char + unique_number

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
            change_wallet_amount(config_queue_obj.custumer.userid, -1 * config_queue_obj.price)
            config_queue_obj.sent_to_user = 3
            cls.save_config_info(config_queue_obj.config_name, config_queue_obj.config_uuid,
                                 config_queue_obj.server.server_id, config_queue_obj.custumer.userid,
                                 config_queue_obj.price)
            cls.send_config_to_user(config_queue_obj.custumer.userid, config_uuid,
                                    config_queue_obj.server.server_id, config_queue_obj.config_name)
        else:
            config_queue_obj.sent_to_user = 5
            config_queue_obj.save()
            if not by_celery:
                CommandRunner.send_msg_to_user(config_queue_obj.custumer.userid,
                                               '🟢 کابر گرامی کانفیگ شما تا دقایقی دیگر به صورت خودکار برای شما ارسال میشود.')

    @classmethod
    def create_config_from_wallet(cls, chat_id, server_id, expire_limit, usage_limit, user_limit, price):
        from connection.command_runer import CommandRunner
        server_obj = ServerModel.objects.get(server_id=server_id)
        conf_uuid = str(uuid.uuid4())
        config_name = Configs.generate_unique_name()
        create_config = ServerApi.create_config(server_id, config_name, conf_uuid, usage_limit, expire_limit * 30,
                                                user_limit, True)
        if create_config:
            vless = cls.create_vless_text(conf_uuid, server_obj, config_name)
            CommandRunner.send_msg_to_user(chat_id, vless)
            change_wallet_amount(chat_id, -1 * price)
            cls.save_config_info(config_name, conf_uuid, server_id, chat_id, price)
            return True
        return False

    @classmethod
    def create_config_by_admins(cls, server_id, expire_limit, usage_limit, user_limit, price, paid, created_by, request):
        conf_uuid = uuid.uuid4()
        config_name = Configs.generate_unique_name()
        create_config = ServerApi.create_config(server_id, config_name, conf_uuid, usage_limit, expire_limit * 30,
                                                user_limit, True)
        if create_config:
            cls.save_config_info(config_name, conf_uuid, server_id, None, price, paid, created_by)
            return {'config_name':config_name, 'config_uuid':conf_uuid}
        return None


# TODO: save config price

class ListConfigs(LoginRequiredMixin, View):
    def get(self, request, server_id, *args, **kwargs):
        data = ServerApi.get_list_configs(server_id)
        if not data:
            messages.error(request,
                           f"اتصال به سرور {ServerModel.objects.get(server_id=server_id).server_name} برقرار نشد.")
        searchform = SearchForm()
        return render(request, "list_configs.html", {"data": data, 'searchform': searchform, 'server_id':server_id})

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
            return render(request, "list_configs_searched.html", {"configs_model": model_obj, "search_config": form})
        return redirect('accounts:home')


class ConfigPage(LoginRequiredMixin, View):
    def get(self, request, server_id, config_uuid, config_name):
        if ConfigsInfo.objects.filter(config_uuid=config_uuid).exists():
            config_info = ConfigsInfo.objects.get(config_uuid=config_uuid)
        else:
            config_info = False
        config_usage = ServerApi.get_config(server_id, config_name)
        get_config_link = f'tg://resolve?domain={BOT_USERNAME}&start=register_{config_uuid}'
        vless = Configs.create_vless_text(config_uuid, ServerModel.objects.get(server_id=server_id), config_name)
        return render(request, 'config_page.html', {'config_info': config_info,'vless':vless,
                            'config_usage': config_usage, 'config_name':config_name, "get_config_link": get_config_link})


class CreateConfigPage(LoginRequiredMixin, View):
    def get(self, request, server_id, form_type):
        forms = {'auto': CreateConfigForm, 'manual': ManualCreateConfigForm}
        return render(request, 'create_config.html',
                      {'server_id': server_id, 'form': forms[form_type], 'form_type': form_type})

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
            create_config = Configs.create_config_by_admins(server_id, time_limit, usage, ip_limit, price, paid, request.user.username, request),
            print(create_config)
            if create_config[0]:
                print('dfvsdfvdfsvbsdgb')
                return redirect('servers:conf_page', server_id, create_config[0]["config_uuid"], create_config[0]["config_name"])

            messages.error(request,"اتصال به سرور برقرار نشد.")

        return render(request, 'create_config.html', {'server_id': server_id, 'form': form, 'form_type': form_type})


class ApiGetConfigTimeChoices(APIView):
    def get(self, request):
        sleep(0.5)
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
        print(time)
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
        print(time, iplimit, usage)
        obj = PricesModel.objects.get(usage_limit=usage, expire_limit=time, user_limit=iplimit).price
        print(obj)
        return Response({'price': f'{obj:,}'})


class DeleteConfig(LoginRequiredMixin, View):
    def get(self, request, server_id, config_uuid, config_name, inbound_id):
        delete = ServerApi.delete_config(server_id, config_uuid , inbound_id)
        if delete:
            messages.success(request, f"کانفیگ {config_name} با موفقیت حذف شد.")
            if ConfigsInfo.objects.filter(config_uuid=config_uuid).exists():
                obj = ConfigsInfo.objects.get(config_uuid=config_uuid)
                obj.delete()

        else:
            messages.error(request, "ارور در حذف کانفیگ")
        return redirect('servers:list_configs', server_id)


class DisableConfig(LoginRequiredMixin, View):
    def get(self,request ,server_id, config_uuid, inbound_id, config_name, enable, ip_limit):
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
                    ServerApi.disable_config(session,server_id, config_uuid, inbound_id, config_name, bool(enable), ip_limit, obj['expiryTime'], obj['total'])
                    return redirect('servers:list_configs', server_id)