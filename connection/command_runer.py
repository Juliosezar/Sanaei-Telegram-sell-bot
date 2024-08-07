from os import environ
from finance.views import Wallet
import requests
from custumers.views import Customer
import json
from custumers.models import Customer as CustumerModel
from servers.models import Server as ServerModel, CreateConfigQueue, ConfigsInfo, TamdidConfigQueue, TestConfig
from finance.views import Prices
from finance.models import Prices as PricesModel
from finance.models import ConfirmPaymentQueue as ConfirmPaymentQueueModel
from finance.models import ConfirmTamdidPaymentQueue as TamdidConfirmPaymentQueueModel
from finance.views import Paying
from finance.models import OffCodes, UserActiveOffCodes
from django.conf import settings
from servers.views import Configs
from uuid import uuid4
from django.core.files.base import ContentFile
from .models import SendMessage
from uuid import UUID
from servers.views import ServerApi
from persiantools.jdatetime import JalaliDateTime
import qrcode
from reports.models import ErrorLog


def is_valid_uuid(uuid_to_test):
    try:
        uuid_obj = UUID(uuid_to_test, version=4)
    except ValueError:
        return False
    return str(uuid_obj) == uuid_to_test


TOKEN = environ.get('TELEGRAM_TOKEN')
TELEGRAM_SERVER_URL = f"https://api.telegram.org/bot{TOKEN}/"


def args_spliter(args):
    return args.split("<%>")


class CommandRunner:
    @classmethod
    def send_api(cls, api_method, data):
        url = TELEGRAM_SERVER_URL + api_method
        try:
            # print(data)
            response = requests.post(url, json=data, timeout=3)
            # print(response.json())
            return response
        except requests.exceptions.RequestException as e:
            ErrorLog.objects.create(
                error=e,
                timestamp=int(JalaliDateTime.now().timestamp())
            )
            return False
        # TODO : log error

    @classmethod
    def download_photo(cls, file_id, chat_id, config_in_queue, for_tamdid=False):
        file_info = requests.get(f"https://api.telegram.org/bot{TOKEN}/getFile?file_id={file_id}").json()["result"]
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info['file_path']}"
        img_data = requests.get(file_url).content
        user_obj = CustumerModel.objects.get(userid=chat_id)
        if for_tamdid:
            cpq_obj = TamdidConfirmPaymentQueueModel.objects.get(config__chat_id=user_obj, status=0)
            cpq_obj.image.save(file_id + ".jpg", ContentFile(img_data), save=False)
            cpq_obj.status = 1
            cpq_obj.save()
            tmdid_obj = TamdidConfigQueue.objects.get(config__chat_id=user_obj, pay_status=0)
            tmdid_obj.pay_status = 1
            tmdid_obj.save()
        else:
            cpq_obj = ConfirmPaymentQueueModel.objects.get(custumer=user_obj, status=0)
            cpq_obj.image.save(file_id + ".jpg", ContentFile(img_data), save=False)
            cpq_obj.status = 1
            cpq_obj.save()
            if config_in_queue:
                cq = CreateConfigQueue.objects.get(custumer=user_obj, pay_status=0, sent_to_user=False)
                cq.pay_status = 1
                cq.save()

    @classmethod
    def send_msg_to_user(cls, chat_id, msg, keyboard=False):
        for i in ['_', '*', '[', ']', '(', ')', '~', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']:
            msg = msg.replace(i, f"\\{i}")
        data = {'chat_id': chat_id,
                'text': msg,
                'parse_mode': 'MarkdownV2',
                }
        if keyboard:
            data['reply_markup'] = {"inline_keyboard": [keyboard]}
        respons = cls.send_api("sendMessage", data)
        if not respons:
            SendMessage.objects.create(customer=CustumerModel.objects.get(userid=chat_id), message=msg)
        return True

    @classmethod
    def celery_send_msg(cls, chat_id, msg):
        for i in ['_', '*', '[', ']', '(', ')', '~', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']:
            msg = msg.replace(i, f"\\{i}")
        data = {'chat_id': chat_id,
                'text': msg,
                'parse_mode': 'MarkdownV2',
                }
        try:
            url = TELEGRAM_SERVER_URL + 'sendMessage'
            response = requests.post(url, json=data, timeout=3)
            if response.status_code == 200:
                return 'Succes'
            elif response.status_code == 403:
                return 'Banned'
            else:
                return 'Faild'
        except requests.exceptions.Timeout:
            return 'Timeout'
        except requests.exceptions.SSLError or requests.exceptions.BaseHTTPError or requests.exceptions.ConnectionError \
               or requests.exceptions.RetryError or requests.exceptions.HTTPError or requests.exceptions.RequestException:
            return 'Faild'
        except Exception as e:
            return 'Error'

    # TODO : log error

    @classmethod
    def abort(cls, chat_id, *args):
        cls.send_msg_to_user(chat_id, "❌ عملیات لغو شد.❗️")
        cls.main_menu(chat_id)

    @classmethod
    def get_user_info(cls, chat_id, *args):
        data = {'chat_id': chat_id}
        info = CommandRunner.send_api("getChat", data)
        info = info.json()
        if "username" in info["result"]:
            username = info["result"]["username"]
        else:
            username = None

        if "first_name" in info["result"]:
            first_name = info["result"]["first_name"]
        else:
            first_name = ""

        return {"username": username, "first_name": first_name}

    @classmethod
    def welcome(cls, chat_id, *args):
        cls.send_msg_to_user(chat_id, "به بات فروش NAPSV VPN خوش آمدید.")

    @classmethod
    def main_menu(cls, chat_id, *args):
        user_info = CommandRunner.get_user_info(chat_id)
        if not Customer.check_custumer_info(chat_id, user_info["first_name"], user_info["username"]):
            cls.welcome(chat_id)
        Customer.change_custimer_temp_status(chat_id, "normal")

        data = {
            'chat_id': chat_id,
            'text': '🏠 منوی اصلی 🏠',
            'reply_markup': {
                'keyboard': [
                    [{'text': 'خرید سرویس 🛍'}],
                    [{'text': 'سرویس های من 🧑‍💻'}],
                    [{'text': 'ارتباط با ادمین 👤'}],
                    [{'text': 'تست رایگان 🔥'}, {'text': 'کیف پول 💰'}],
                    [{'text': 'تعرفه ها 💳'}, {'text': 'آیدی من 🆔'}],
                    [{'text': '💻📱 دانلود اپلیکیشن و راهنمای اتصال 💡'}],
                ],
                'resize_keyboard': True,
                'one_time_keyboard': True,
                'is_persistent': False,
            }
        }
        cls.send_api("sendMessage", data)

    @classmethod
    def show_wallet_status(cls, chat_id, *args):
        amount = (Wallet.get_wallet_anount(chat_id))
        amount = f"{amount:,}"
        data = {
            'chat_id': chat_id,
            'text': f' 🟢 موجودی کیف پول شما : \n\n💵 *{amount}* تومان ',
            'reply_markup': {
                'inline_keyboard': [
                    [{'text': '➕ افزایش موجودی 💲', 'callback_data': 'add_to_wallet<~>'}],
                ]
            },
            'parse_mode': 'Markdown',
        }
        cls.send_api("sendMessage", data)

    @classmethod
    def set_pay_amount(cls, chat_id, *args):
        Customer.change_custimer_temp_status(chat_id, "set_pay_amount")
        data = {
            'chat_id': chat_id,
            "text": "مبلغ مورد نظر را خود را به تومان وارد کنید :",
            'reply_markup': {
                'keyboard': [
                    [{'text': '❌ لغو پرداخت 💳'}],
                ],
                'resize_keyboard': True,
                'one_time_keyboard': True,
            }
        }
        cls.send_api("sendMessage", data)

    @classmethod
    def send_pay_card_info(cls, chat_id, *args):
        amount = args[0]
        if amount.isnumeric():
            amount = int(amount)
            if 2000 <= amount < 1000000:
                with open(settings.BASE_DIR / 'settings.json', 'r') as f:
                    data = json.load(f)
                    card_num = data["pay_card_number"]
                    card_name = data["pay_card_name"]
                data = {
                    'chat_id': chat_id,
                    'text': f" مبلغ {amount}تومان را به شماره کارت زیر انتقال دهید، سپس عکس آنرا بعد از همین پیام ارسال نمایید : " + f'\n\n`{card_num}`\n {card_name}',
                    'parse_mode': 'Markdown',
                }

                Customer.change_custimer_temp_status(chat_id, "get_paid_picture")
                Paying.pay_to_wallet_before_img(chat_id, amount)
                cls.send_api("sendMessage", data)
            else:
                cls.send_msg_to_user(chat_id, "حداقل مقدار پرداختی 2000 تومان است. دوباره وارد کنید :")
        else:
            cls.send_msg_to_user(chat_id, "مقدار را به صورت لاتین(انگلیسی) و به تومان وارد کنید :")

    @classmethod
    def contact_us(cls, chat_id, *args):
        data = {
            'chat_id': chat_id,
            'text': f' با سلام خدمت شما کاربر گرامی \n\n' + "🟢 پشتیبانی از 8 صبح تا 12 شب 👇\n" + "🆔 @NapsV_supp"
        }
        cls.send_api("sendMessage", data)

    @classmethod
    def select_server(cls, chat_id, *args):
        server_obj = ServerModel.objects.filter(active=True, iphone=False)
        keyboard_list = []
        for i in server_obj:
            keyboard_list.append(
                [{'text': i.server_name, 'callback_data': f"server_buy<~>{i.server_id}"}]
            )
        data = {
            'chat_id': chat_id,
            'text': '🌐 سرور مورد نظر خود را انتخاب کنید 👇🏻',
            'reply_markup': {
                'inline_keyboard': keyboard_list
            },
        }
        cls.send_api("sendMessage", data)

    @classmethod
    def back_to_select_server(cls, chat_id, *args):
        msg_id = int(args[0])
        server_obj = ServerModel.objects.filter(active=True, iphone=False)
        keyboard_list = []
        for i in server_obj:
            keyboard_list.append(
                [{'text': i.server_name, 'callback_data': f"server_buy<~>{i.server_id}"}]
            )
        data = {
            'chat_id': chat_id,
            'message_id': msg_id,
            'text': '🌐 سرور مورد نظر خود را انتخاب کنید 👇🏻',
            'reply_markup': {
                'inline_keyboard': keyboard_list
            },
        }
        cls.send_api("editMessageText", data)

    @classmethod
    def select_config_expire_time(cls, chat_id, *args):
        server_id = args[1]
        msg_id = int(args[0])
        month_list = []
        for m in Prices.get_expire_times():
            if m == 0:
                m_text = " ♾ " + "زمان نامحدود"
            else:
                m_text = " 🔘 " + f"{m} ماهه"
            month_list.append([{'text': f"{m_text}", 'callback_data': f"expire_time<~>{server_id}<%>{m}"}])
        month_list.append([{'text': '🔙 بازگشت', 'callback_data': f"back_to_servers<~>"}])
        server_name = ServerModel.objects.get(server_id=server_id).server_name
        data = {
            'chat_id': chat_id,
            'message_id': msg_id,
            'text': f' 🌍 سرور: {server_name} \n\n' + '⏱ مدت زمان سرویس خود را انتخاب کنید 👇🏻',
            'reply_markup': {
                'inline_keyboard': month_list
            },
        }
        cls.send_api("editMessageText", data)

    @classmethod
    def select_config_usage(cls, chat_id, *args):
        msg_id = int(args[0])
        arg_splited = args_spliter(args[1])
        server_id = arg_splited[0]
        expire_month = int(arg_splited[1])
        price_obj = Prices.get_usage_and_prices_of_selected_month(expire_month)
        usage_list = []
        for u in price_obj:
            if u.usage_limit == 0:
                u_text = " ♾ " + "نامحدود" + " - " + f"{u.user_limit} کاربره" + " - " + f"{u.price} تومان "
            else:
                u_text = " 🔘 " + f"{u.usage_limit} گیگ" + " - " + f"{u.price} تومان "
            usage_list.append([{'text': u_text,
                                'callback_data': f"usage_limit<~>{server_id}<%>{expire_month}<%>{u.usage_limit}<%>{u.user_limit}"}])
        usage_list.append([{'text': '🔙 بازگشت', 'callback_data': f"server_buy<~>{server_id}"}])
        server_name = ServerModel.objects.get(server_id=server_id).server_name

        if expire_month == 0:
            choosen = " زمان نامحدود ♾ "
        else:
            choosen = f" {expire_month} ماهه"

        text = f' 🌍 سرور:  {server_name} \n\n' + f' ⏱ انقضا: {choosen}\n\n' + '🔃 حجم کانفیگ خود را انتخاب کنید 👇🏻'
        data = {
            'chat_id': chat_id,
            'message_id': msg_id,
            'text': text,
            'reply_markup': {
                'inline_keyboard': usage_list
            },
        }
        cls.send_api("editMessageText", data)

    @classmethod
    def confirm_config_buying(cls, chat_id, *args):
        msg_id = int(args[0])
        arg_splited = args_spliter(args[1])
        server_id = arg_splited[0]
        expire_month = int(arg_splited[1])
        usage_limit = int(arg_splited[2])
        user_limit = int(arg_splited[3])
        custumer_obj = CustumerModel.objects.get(userid=chat_id)
        wallet_amount = custumer_obj.wallet
        price = PricesModel.objects.get(expire_limit=expire_month, user_limit=user_limit, usage_limit=usage_limit).price
        wallet_amount_text = f"{wallet_amount:,}"
        have_off_code = False
        text = ""
        if expire_month == 0:
            expire_month_text = " زمان نامحدود ♾"
            if UserActiveOffCodes.objects.filter(custumer__userid=chat_id, used=False, off_code__for_infinit_times=True).exists():
                have_off_code = True
        else:
            expire_month_text = f" {expire_month} ماهه"
        if usage_limit == 0:
            usage_limit_text = ' نامحدود ♾'
            if UserActiveOffCodes.objects.filter(custumer__userid=chat_id, used=False,off_code__for_infinit_usages=True).exists():
                have_off_code = True
        else:
            usage_limit_text = f'{usage_limit} GB'

        if usage_limit != 0 and expire_month != 0 and UserActiveOffCodes.objects.filter(custumer__userid=chat_id,
                                                                    used=False, off_code__for_not_infinity=True).exists():
            have_off_code = True

        if user_limit == 0:
            user_limit_text = ' بدون محدودیت ♾'
        else:
            user_limit_text = user_limit
        server_name = ServerModel.objects.get(server_id=server_id).server_name

        if have_off_code:
            text = "🟢 کد تخفیف شما صورت گرفت و از هزینه سرویس کم گردید." "\n\n"
            off_model = UserActiveOffCodes.objects.get(custumer__userid=chat_id, used=False)
            if off_model.off_code.type_off:
                price = price - int(off_model.off_code.amount * price / 100)
            else:
                price = price - (off_model.off_code.amount * 1000)
        price_text = f"{price:,}"
        pay_amount = price - wallet_amount
        pay_amount_text = f"{pay_amount:,}"
        if wallet_amount >= price:

            data = {
                'chat_id': chat_id,
                'message_id': msg_id,
                'text':text + f' 🌍 سرور:  {server_name} \n' + f' ⏱ انقضا: {expire_month_text}\n'
                                                        f' 🔃 حجم : {usage_limit_text} \n' + f' 👤 محدودیت کاربر: {user_limit_text}\n\n' + f' 💵 هزینه سرویس: {price_text} تومان \n\n'
                                                                                                                                         f'کاربر گرامی، موجودی کیف پول شما {wallet_amount_text} تومان است، برای فعال سازی این سرویس مبلغ {price_text}'
                        + f' تومان از کیف پول شما کسر خواهد شد.\n تایید خرید 👇🏻',
                'reply_markup': {
                    'inline_keyboard': [[{'text': '✅ تایید خرید 💳',
                                          'callback_data': f'buy_config_from_wallet<~>{server_id}<%>{expire_month}<%>{usage_limit}<%>{user_limit}'}],
                                        [{"text": '🔙 بازگشت',
                                          'callback_data': f"expire_time<~>{server_id}<%>{expire_month}"}],
                                        [{'text': 'انصراف ❌', 'callback_data': 'abort_buying'}]]
                },
            }
        else:
            if wallet_amount == 0:
                text_pay = f'کاربر گرامی، برای فعال سازی این سرویس مبلغ {pay_amount_text}'
            else:
                text_pay = f'کاربر گرامی، موجودی کیف پول شما {wallet_amount_text} تومان است، برای فعال سازی این سرویس مبلغ {pay_amount_text}'
            data = {
                'chat_id': chat_id,
                'message_id': msg_id,
                'text': text + f' 🌍 سرور:  {server_name} \n' + f' ⏱ انقضا: {expire_month_text}\n'
                                                               f' 🔃 حجم : {usage_limit_text} \n' + f' 👤 محدودیت کاربر: {user_limit_text}\n\n' + f' 💵 هزینه سرویس: {price_text} تومان \n\n'
                        + text_pay + f' تومان را پرداخت کنید 👇🏻',
                'reply_markup': {
                    'inline_keyboard': [[{'text': '✅ پرداخت / کارت به کارت 💳',
                                          'callback_data': f'pay_for_config<~>{server_id}<%>{expire_month}<%>{usage_limit}<%>{user_limit}'}],
                                        [{"text": '🔙 بازگشت',
                                          'callback_data': f"expire_time<~>{server_id}<%>{expire_month}"}],
                                        [{'text': 'انصراف ❌', 'callback_data': 'abort_buying'}]]
                },
            }
        cls.send_api("editMessageText", data)

    @classmethod
    def pay_for_config(cls, chat_id, *args):
        msg_id = args[0]
        arg_splited = args_spliter(args[1])
        server_id = arg_splited[0]
        expire_limit = int(arg_splited[1])
        usage_limit = int(arg_splited[2])
        user_limit = int(arg_splited[3])
        price = PricesModel.objects.get(usage_limit=usage_limit, expire_limit=expire_limit, user_limit=user_limit).price
        have_off_code = False
        if usage_limit != 0 and expire_limit != 0 and UserActiveOffCodes.objects.filter(custumer__userid=chat_id, used=False, off_code__for_not_infinity=True).exists():
            have_off_code = True
        elif usage_limit == 0 and UserActiveOffCodes.objects.filter(custumer__userid=chat_id, used=False, off_code__for_infinit_usages=True).exists():
            have_off_code = True
        elif expire_limit == 0 and UserActiveOffCodes.objects.filter(custumer__userid=chat_id, used=False, off_code__for_infinit_times=True).exists():
            have_off_code = True
        if have_off_code:
            off_model = UserActiveOffCodes.objects.get(custumer__userid=chat_id, used=False)
            if off_model.off_code.type_off:
                price = price - int(off_model.off_code.amount * price / 100)
            else:
                price = price - (off_model.off_code.amount * 1000)
        wallet = CustumerModel.objects.get(userid=chat_id).wallet
        with open(settings.BASE_DIR / 'settings.json', 'r') as f:
            data = json.load(f)
            card_num = data["pay_card_number"]
            card_name = data["pay_card_name"]
        data = {
            'message_id': msg_id,
            'chat_id': chat_id,
            'text': f" مبلغ {price - wallet} تومان را به شماره کارت زیر انتقال دهید، سپس عکس آنرا بعد از همین پیام ارسال نمایید : " + f'\n\n`{card_num}`\n {card_name}',
            'parse_mode': 'Markdown',
        }
        data2 = {
            'chat_id': chat_id,
            "text": "تصویر پرداختی خود را ارسال کنید :",
            'resize_keyboard': True,
            'one_time_keyboard': True,
            'reply_markup': {
                'keyboard': [
                    [{'text': '❌ لغو پرداخت 💳'}]]
            },
        }
        Customer.change_custimer_temp_status(chat_id, "get_paid_picture_for_config")
        uu_id = uuid4()
        Paying.pay_config_before_img(chat_id, price, uu_id)
        Configs.add_configs_to_queue_before_confirm(server_id, chat_id, uu_id, usage_limit, expire_limit * 30,
                                                    user_limit, price)
        # expire limit * 30
        cls.send_api("sendMessage", data2)
        cls.send_api("editMessageText", data)

    @classmethod
    def buy_config_from_wallet(cls, chat_id, *args):
        msg_id = int(args[0])
        arg_splited = args_spliter(args[1])
        server_id = arg_splited[0]
        expire_limit = int(arg_splited[1])
        usage_limit = int(arg_splited[2])
        user_limit = int(arg_splited[3])
        price = PricesModel.objects.get(usage_limit=usage_limit, expire_limit=expire_limit, user_limit=user_limit).price
        have_off_code = False
        if usage_limit != 0 and expire_limit != 0 and UserActiveOffCodes.objects.filter(custumer__userid=chat_id,
                                                                                        used=False,
                                                                                        off_code__for_not_infinity=True).exists():
            have_off_code = True
        elif usage_limit == 0 and UserActiveOffCodes.objects.filter(custumer__userid=chat_id, used=False,
                                                                    off_code__for_infinit_usages=True).exists():
            have_off_code = True
        elif expire_limit == 0 and UserActiveOffCodes.objects.filter(custumer__userid=chat_id, used=False,
                                                                     off_code__for_infinit_times=True).exists():
            have_off_code = True
        if have_off_code:
            off_model = UserActiveOffCodes.objects.get(custumer__userid=chat_id, used=False)
            if off_model.off_code.type_off:
                price = price - int(off_model.off_code.amount * price / 100)
            else:
                price = price - (off_model.off_code.amount * 1000)
        create_config = Configs.create_config_from_wallet(chat_id, server_id, expire_limit, usage_limit, user_limit, price)
        if create_config:
            data = {
                'message_id': msg_id,
                'chat_id': chat_id,
                'text': f"کانفیک شما ارسال شد و مبلغ {price} تومان از کیف پول شما کسر شد.",
                'parse_mode': 'Markdown',
            }
            cls.send_api("editMessageText", data)
        else:
            msg = f'اتصال به سرور {ServerModel.objects.get(server_id=server_id).server_name} برقرار نشد.' '\n میتوانید کشور مورد نظر را تغییر دهید یا دقایقی دیگر دوباره امتحان کنید.'
            data = {
                'message_id': msg_id,
                'chat_id': chat_id,
                'text': msg,
                'parse_mode': 'Markdown',
            }
            cls.send_api("editMessageText", data)

    @classmethod
    def abort_buying(cls, chat_id, *args):
        msg_id = int(args[0])
        data = {
            'message_id': msg_id,
            'chat_id': chat_id,
            'text': f'خرید شما لغو شد. ❌',
            'parse_mode': 'Markdown',
        }
        cls.send_api("editMessageText", data)
        cls.main_menu(chat_id)

    @classmethod
    def register_config(cls, chat_id, msg):
        if is_valid_uuid(msg):
            if ConfigsInfo.objects.filter(config_uuid=msg).exists():
                custumer = CustumerModel.objects.get(userid=chat_id)
                obj = ConfigsInfo.objects.get(config_uuid=msg)
                obj.chat_id = custumer
                obj.save()
                vless = Configs.create_vless_text(msg, obj.server, obj.config_name)
                cls.send_msg_to_user(chat_id, "🟢 کانفیگ شما ثبت شد.")
                data = {
                    'chat_id': chat_id,
                    'text': vless,
                    'parse_mode': 'Markdown',
                    'reply_markup': {
                        'inline_keyboard': [[{'text': 'دریافت QRcode',
                                              'callback_data': f'QRcode<~>{msg}'}],
                                            ]

                    },
                }
                cls.send_api("sendMessage", data)
            else:
                cls.send_msg_to_user(chat_id, "کانفیگی با این مشخصات ثبت نشده است.")
        else:
            cls.send_msg_to_user(chat_id, 'لینک نامعتبر است.')

    @classmethod
    def Qrcode(cls, chat_id, *args):
        conf_uuid = args[1]
        if ConfigsInfo.objects.filter(config_uuid=conf_uuid).exists():
            obj = ConfigsInfo.objects.get(config_uuid=conf_uuid)
            vless = (f"vless://{obj.config_uuid}@{obj.server.server_fake_domain}:{obj.server.inbound_port}?"
                     f"security=none&encryption=none&host=speedtest.net&headerType=http&type=tcp#{obj.config_name}"
                     )
            qr = qrcode.QRCode(version=3, box_size=30, border=10, error_correction=qrcode.constants.ERROR_CORRECT_H)
            qr.add_data(vless)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            filename = conf_uuid
            img.save(str(settings.MEDIA_ROOT) + f"/{filename}.jpg")
            data = {'chat_id': chat_id,
                    'photo': f"https://admin-napsv.ir/media/{filename}.jpg",
                    "caption": f" 💠 سرویس: {obj.config_name}"}
            cls.send_api("sendPhoto", data)

        else:
            cls.send_msg_to_user(chat_id, "سرویس ثبت نشده است.")

    @classmethod
    def myid(cls, chat_id, *args):
        cls.send_msg_to_user(chat_id, '👤 آیدی شما : \n ' f'🆔 `{chat_id}`')

    @classmethod
    def send_prices(cls, chat_id, *args):
        with open(settings.BASE_DIR / 'settings.json', 'r') as f:
            data = json.load(f)
            msg_id = data["prices_msg_id"]

        data = {
            'chat_id': chat_id,
            'from_chat_id': environ.get("SIDE_CHANNEL_USERNAME"),
            'message_id': msg_id
        }
        cls.send_api("copyMessage", data)

    @classmethod
    def my_services(cls, chat_id, *args):
        services = ConfigsInfo.objects.filter(chat_id__userid=chat_id)
        opts = []
        for service in services:
            opts.append([{'text': " 🔗 " + service.config_name + "\n" + service.server.server_name,
                          'callback_data': f'service_status<~>{service.config_uuid}'}])
        data = {
            'chat_id': chat_id,
            'text': '🌐 سرویس های شما 👇🏻',
            'parse_mode': 'Markdown',
            'reply_markup': {
                'inline_keyboard': opts

            },
        }
        if services.count() == 0:
            data = {
                'chat_id': chat_id,
                'text': 'شما سرویس ثبت شده ای ندارید.',
                'parse_mode': 'Markdown',
            }

        if args:
            msg_id = int(args[0])
            data["message_id"] = msg_id
            cls.send_api("editMessageText", data)
        else:
            cls.send_api("sendMessage", data)

    @classmethod
    def get_service(cls, chat_id, *args):
        msg_id = int(args[0])
        arg_splited = args_spliter(args[1])
        conf_uuid = arg_splited[0]
        keybord = []
        if ConfigsInfo.objects.filter(config_uuid=conf_uuid).exists():
            keybord.append([{'text': '🔄 Refresh 🔄', 'callback_data': f'service_status<~>{conf_uuid}'}])
            service = ConfigsInfo.objects.get(config_uuid=conf_uuid)
            text = '🔰 نام سرویس: ' + f'{service.config_name}' '\n\n' '🌐 سرور: ' f"{service.server.server_name}"
            api = ServerApi.get_config(service.server.server_id, service.config_name)
            if api:
                usage = round(api['usage'], 2)
                usage_limit = api['usage_limit']
                kind = "حجمی"
                if usage_limit == 0:
                    kind = "حجم نامحدود"
                    usage_limit = "♾"
                elif api['time_expire'] == 0:
                    usage_limit = str(usage_limit) + "GB"
                    kind = "حجمی / زمان نامحدود"
                expire_days = api['time_expire']
                if expire_days == 0:
                    expire_days = "♾"
                elif api['expired']:
                    expire_days = "اتمام اشتراک ❌"
                else:
                    hour = int((abs(expire_days) % 1) * 24)
                    day = abs(int(expire_days))
                    expire_days = f" {day} روز" f' و {hour} ساعت '
                if usage == 0:
                    status = "استارت نشده 🔵"
                    keybord.append(
                        [{'text': '🌐 تغییر لوکیشن سرور 🌐', 'callback_data': f'choose_location<~>{conf_uuid}'}])
                elif api["ended"]:
                    status = "فعال 🟢"
                    keybord.append(
                        [{'text': '🌐 تغییر لوکیشن سرور 🌐', 'callback_data': f'choose_location<~>{conf_uuid}'}])
                else:
                    status = "تماما شده 🔴"
                    keybord.append([{'text': '♻️ تمدید ♻️', 'callback_data': f'tamdid<~>{conf_uuid}'}])
                text += '\n\n' "📥 حجم مصرفی: " f'{usage}GB از {usage_limit}' '\n\n' '⏳ روز های باقی مانده: ' f'{expire_days}' '\n\n' '📶 وضعیت: ' f'{status}' '\n\n' f'⚙️ نوع: ' f'{kind}'
                text += "\n\n" " برای آپدیت اطلاعات بالا بر روی دکمه (Refresh) کلیک کنید 👇"
            else:
                text += "\n\n" + f"اتصال به سرور {service.server.server_name} برقرار نشد، دقایقی دیگر با زدن بر روی دکمه (Refresh) دوباره امتحان کنید 👇🏻"
        else:
            text = '❌ این سرویس دیگر فعال نیست.'
        text = text.replace('_', "\\_")
        keybord.append([{'text': 'دریافت QRCode', 'callback_data': f"QRcode<~>{conf_uuid}"}])
        keybord.append([{'text': '🔙 بازگشت', 'callback_data': f"سرویس های من 🧑‍💻"}])
        data = {
            'chat_id': chat_id,
            'message_id': msg_id,
            'text': text,
            'parse_mode': 'Markdown',
            'reply_markup': {
                'inline_keyboard': keybord
            },
        }
        cls.send_api("editMessageText", data)

    @classmethod
    def choose_location(cls, chat_id, *args):
        msg_id = int(args[0])
        arg_splited = args_spliter(args[1])
        conf_uuid = arg_splited[0]
        if ConfigsInfo.objects.filter(config_uuid=conf_uuid).exists():
            service = ConfigsInfo.objects.get(config_uuid=conf_uuid)
            keyboard = []
            for i in ServerModel.objects.filter(active=True, iphone=service.server.iphone):
                if i.server_id != service.server.server_id:
                    keyboard.append([{'text': f'{i.server_name}',
                                      'callback_data': f'change_location<~>{conf_uuid}<%>{i.server_id}'}])

            keyboard.append([{'text': '🔙 بازگشت', 'callback_data': f'service_status<~>{conf_uuid}'}])
            data = {
                'chat_id': chat_id,
                'message_id': msg_id,
                'text': f"سرویس: {service.config_name}" "\n\n" f"🌐 سرور فعلی : {service.server.server_name}" "\n\n" "سرور مورد نظر را برای انتقال انتخاب کنید 👇🏻",
                'reply_markup': {
                    'inline_keyboard': keyboard
                },
            }
        else:
            data = {
                'chat_id': chat_id,
                'message_id': msg_id,
                'text': f"سرویس پیدا نشد.",
                'reply_markup': {
                    'inline_keyboard': [
                        [{'text': '🔙 بازگشت', 'callback_data': f'service_status<~>{conf_uuid}'}]
                    ]
                },
            }
        cls.send_api("editMessageText", data)

    @classmethod
    def change_location(cls, chat_id, *args):
        msg_id = int(args[0])
        arg_splited = args_spliter(args[1])
        conf_uuid = arg_splited[0]
        server_to = arg_splited[1]
        if ConfigsInfo.objects.filter(config_uuid=conf_uuid).exists():
            service = ConfigsInfo.objects.get(config_uuid=conf_uuid)
            server_to = ServerModel.objects.get(server_id=server_to)
            data = {
                'chat_id': chat_id,
                'message_id': msg_id,
                'text': f"آیا از انتقال سرویس {service.config_name} از سرور {service.server.server_name} به {server_to.server_name} مطمئنید؟",
                'reply_markup': {
                    'inline_keyboard': [
                        [{'text': '🛰 تایید انتقال ✅',
                          'callback_data': f'confirm_change<~>{conf_uuid}<%>{server_to.server_id}'}],
                        [{'text': '🔙 بازگشت', 'callback_data': f'service_status<~>{conf_uuid}'}]
                    ]
                },
            }
        else:
            data = {
                'chat_id': chat_id,
                'message_id': msg_id,
                'text': f"سرویس پیدا نشد.",
                'reply_markup': {
                    'inline_keyboard': [
                        [{'text': '🔙 بازگشت', 'callback_data': f'service_status<~>{conf_uuid}'}]
                    ]
                },
            }
        cls.send_api("editMessageText", data)

    @classmethod
    def confirm_change(cls, chat_id, *args):
        msg_id = int(args[0])
        arg_splited = args_spliter(args[1])
        conf_uuid = arg_splited[0]
        server_to = int(arg_splited[1])
        if ConfigsInfo.objects.filter(config_uuid=conf_uuid).exists():
            service = ConfigsInfo.objects.get(config_uuid=conf_uuid)
            data = {
                'chat_id': chat_id,
                'message_id': msg_id,
                'text': f"🟢 درخواست انتقال شما ثبت شد و تا لحظاتی دیگر نتیجه اعلام میشود.",
            }
            cls.send_api("editMessageText", data)
            if (int(JalaliDateTime.now().timestamp()) - service.change_location_time) > 604800:
                api = ServerApi.change_location(service.server.server_id, server_to, conf_uuid)
                if api == "ended":
                    cls.send_msg_to_user(chat_id,
                                         "کانفیگ شما به اتمام رسیده یا توسط ادمین غیرفعال گردیده است و نمیتوانید سرور آنرا تغییر دهید.")
                elif api:
                    cls.send_msg_to_user(chat_id,
                                         f" ✅ سرویس {service.config_name} با موفقیت انتقال پیدا کرد و برای شما ارسال میشود.")
                    Configs.send_config_to_user(chat_id, conf_uuid, server_to, service.config_name)
                    service.change_location_time = int(JalaliDateTime.now().timestamp())
                    service.server = ServerModel.objects.get(server_id=server_to)
                    service.save()
                else:
                    cls.send_msg_to_user(chat_id,
                                         f" 🔴 انتقال سرویس {service.config_name} با ارور مواجه شد، سرور دیگری برای انتقال انتخاب کنید یا دقایقی دیگر دوباره امتحان کنید.")
            else:
                cls.send_msg_to_user(chat_id,
                                     "🔴 مشتری گرامی، هر سرویس محدودیت انتقال هفته ای یکبار دارد و شما در یک هفته اخیر این سرویس را انتقال داده اید; میتوانید در این مورد به ادمین پیام دهید.")
        else:
            data = {
                'chat_id': chat_id,
                'message_id': msg_id,
                'text': f"سرویس پیدا نشد.",
                'reply_markup': {
                    'inline_keyboard': [
                        [{'text': '🔙 بازگشت', 'callback_data': f'service_status<~>{conf_uuid}'}]
                    ]
                },
            }
        cls.send_api("editMessageText", data)

    @classmethod
    def download_apps(cls, chat_id, *args):
        with open(settings.BASE_DIR/ "settings.json") as f:
            f_data = json.load(f)["applicatios"]
            keybord = []
            for ind,app in enumerate(f_data):
                keybord.append([{"text":app["app_name"], "callback_data": f"down_guid_app<~>{ind}"}])

        data = {
            'chat_id': chat_id,
            'text': '🏻📥 لیست نرم افزار ها به شرح زیر است. متانسب با سیستم عامل خود انتخاب کنید. 👇',
            'parse_mode': 'Markdown',
            'reply_markup': {
                'inline_keyboard': keybord
            },
        }
        cls.send_api("sendMessage", data)

    @classmethod
    def down_guid_app(cls, chat_id, *args):
        print(args)
        msg_id = int(args[0])
        ind = int(args[1])
        print(ind)
        with open(settings.BASE_DIR/ "settings.json") as f:
            f_data = json.load(f)["applicatios"]

        data = {
            'chat_id': chat_id,
            "message_id": msg_id,
            'text': f'{f_data[ind]["app_name"]}' "\n\n" '📥 دانلود / 💡 آموزش استفاده از برنامه 👇' ,
            'parse_mode': 'Markdown',
            'reply_markup': {
                'inline_keyboard': [
                    [{'text': '📥 لینک دانلود برنامه 📥','url': f_data[ind]["download_url"]}],
                    [{'text': '💡 آموزش برنامه 💡', 'callback_data': f"send_guid<~>{f_data[ind]["guid"]}"}],
                ]
            },
        }
        cls.send_api("sendMessage", data)

    @classmethod
    def send_guid(cls, chat_id, *args):
        print(args)
        ind = int(args[1])
        data = {
            'chat_id': chat_id,
            'from_chat_id': environ.get("SIDE_CHANNEL_USERNAME"),
            'message_id': ind
        }
        cls.send_api("copyMessage", data)


    @classmethod
    def send_end_of_config_notif(cls, chat_id, api, *args):
        service = ConfigsInfo.objects.get(config_uuid=api["uuid"])
        text = "‼️ مشتری گرامی، اشتراک سرویس زیر به اتمام رسیده است.🔔 \n\n"
        text += '🔰 نام سرویس: ' + f'{service.config_name}' '\n\n' '🌐 سرور: ' f"{service.server.server_name}"
        usage = round(api['usage'], 2)
        usage_limit = api['usage_limit']
        kind = "حجمی"
        if usage_limit == 0:
            kind = "حجم نامحدود"
            usage_limit = "♾"
        elif api['expire_time'] == 0:
            usage_limit = str(usage_limit) + "GB"
            kind = "حجمی / زمان نامحدود"
        expire_days = api['expire_time']
        if expire_days == 0:
            expire_days = "♾"
        elif api['expired']:
            expire_days = "اتمام اشتراک ❌"
        else:
            hour = int((abs(expire_days) % 1) * 24)
            day = abs(int(expire_days))
            expire_days = f'{hour} ساعت ' f"و {day} روز"
        if usage == 0:
            status = "استارت نشده 🔵"
        elif api["ended"]:
            status = "فعال 🟢"
        else:
            status = "تمام شده 🔴"
        text += '\n' "📥 حجم مصرفی: " f'{usage}GB از {usage_limit}' '\n' '⏳ روز های باقی مانده: ' f'{expire_days}' '\n' '📶 وضعیت: ' f'{status}' '\n' f'⚙️ نوع: ' f'{kind}'
        text += "\n\n" "✅ برای تمدید سرویس بر روی دکمه (تمدید) کلیک کنید 👇"

        text = text.replace('_', "\\_")
        data = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'Markdown',
            'reply_markup': {
                'inline_keyboard': [
                    [{'text': '♻️ تمدید ♻️', 'callback_data': f'tamdid<~>{api["uuid"]}'}], ]
            },
        }
        cls.send_api("sendMessage", data)

    @classmethod
    def send_almost_end_of_config_notif(cls, chat_id, api, type, *args):
        service = ConfigsInfo.objects.get(config_uuid=api["uuid"])
        if type == 0:
            text = "🔶 مشتری گرامی، کمتر از 0.5 گیگ (500مگابایت) از سرویس شما باقی مانده است، برای جلوگیری از قطع شدن سرویس خود آنرا تمدید کنید.🔔 \n\n"
        else:
            text = "🔶 مشتری گرامی، کمتر از 12 ساعت تا اتمام سرویس شما باقی مانده است، برای جلوگیری از قطع شدن سرویس خود آنرا تمدید کنید.🔔 \n\n"
        text += '🔰 نام سرویس: ' + f'{service.config_name}' '\n\n' '🌐 سرور: ' f"{service.server.server_name}"
        usage = round(api['usage'], 2)
        usage_limit = api['usage_limit']
        kind = "حجمی"
        if usage_limit == 0:
            kind = "حجم نامحدود"
            usage_limit = "♾"
        elif api['expire_time'] == 0:
            usage_limit = str(usage_limit) + "GB"
            kind = "حجمی / زمان نامحدود"
        expire_days = api['expire_time']
        if expire_days == 0:
            expire_days = "♾"
        elif api['expired']:
            expire_days = "اتمام اشتراک ❌"
        else:
            hour = int((abs(expire_days) % 1) * 24)
            day = abs(int(expire_days))
            expire_days = f'{hour} ساعت ' f"و {day} روز"
        if usage == 0:
            status = "استارت نشده 🔵"
        elif api["ended"]:
            status = "فعال 🟢"
        else:
            status = "تمام شده 🔴"
        text += '\n' "📥 حجم مصرفی: " f'{usage}GB از {usage_limit}' '\n' '⏳ روز های باقی مانده: ' f'{expire_days}' '\n' '📶 وضعیت: ' f'{status}' '\n' f'⚙️ نوع: ' f'{kind}'
        text += "\n\n" "✅ برای تمدید سرویس بر روی دکمه (تمدید) کلیک کنید 👇"

        text = text.replace('_', "\\_")
        data = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'Markdown',
            'reply_markup': {
                'inline_keyboard': [
                    [{'text': '♻️ تمدید ♻️', 'callback_data': f'tamdid<~>{api["uuid"]}'}], ]
            },
        }
        cls.send_api("sendMessage", data)

    @classmethod
    def tamdid_select_config_expire_time(cls, chat_id, *args):
        msg_id = int(args[0])
        arg_splited = args_spliter(args[1])
        if ConfigsInfo.objects.filter(config_uuid=arg_splited[0]).exists():
            config_info = ConfigsInfo.objects.get(config_uuid=arg_splited[0])
            server_id = config_info.server.server_id
            month_list = []
            for m in Prices.get_expire_times():
                if m == 0:
                    m_text = " ♾ " + "زمان نامحدود"
                else:
                    m_text = " 🔘 " + f"{m} ماهه"
                month_list.append(
                    [{'text': f"{m_text}", 'callback_data': f"tamdid_expire_time<~>{config_info.config_uuid}<%>{m}"}])
            # month_list.append([{'text': '🔙 بازگشت', 'callback_data': f"back_to_servers<~>"}])
            server_name = ServerModel.objects.get(server_id=server_id).server_name
            data = {
                'chat_id': chat_id,
                'message_id': msg_id,
                'text': f"♻️ تمدید سرویس: {config_info.config_name}" "\n\n" f' 🌍 سرور: {server_name} \n\n' + '⏱ مدت زمان سرویس خود را انتخاب کنید 👇🏻',
                'reply_markup': {
                    'inline_keyboard': month_list
                },
            }
            cls.send_api("editMessageText", data)
        else:
            data3 = {
                'chat_id': chat_id,
                "text": "این سرویس حذف شده است و قابل تمدید نیست.",
                'message_id': msg_id,
            }
            cls.send_api("editMessageText", data3)

    @classmethod
    def tamdid_select_config_usage(cls, chat_id, *args):
        msg_id = int(args[0])
        arg_splited = args_spliter(args[1])
        if ConfigsInfo.objects.filter(config_uuid=arg_splited[0]).exists():
            config_info = ConfigsInfo.objects.get(config_uuid=arg_splited[0])
            expire_month = int(arg_splited[1])
            price_obj = Prices.get_usage_and_prices_of_selected_month(expire_month)
            usage_list = []
            for u in price_obj:
                if u.usage_limit == 0:
                    u_text = " ♾ " + "نامحدود" + " - " + f"{u.user_limit} کاربره" + " - " + f"{u.price} تومان "
                else:
                    u_text = " 🔘 " + f"{u.usage_limit} گیگ" + " - " + f"{u.price} تومان "
                usage_list.append([{'text': u_text,
                                    'callback_data': f"tam_usage<~>{config_info.config_uuid}<%>{expire_month}<%>{u.usage_limit}<%>{u.user_limit}"}])
            usage_list.append([{'text': '🔙 بازگشت', 'callback_data': f"tamdid<~>{config_info.config_uuid}"}])
            server_name = config_info.server.server_name
            if expire_month == 0:
                choosen = " زمان نامحدود ♾ "
            else:
                choosen = f" {expire_month} ماهه"
            data = {
                'chat_id': chat_id,
                'message_id': msg_id,
                'text': f"♻️ تمدید سرویس: {config_info.config_name}" "\n\n" f' 🌍 سرور:  {server_name} \n\n' + f' ⏱ انقضا: {choosen}\n\n' + '🔃 حجم کانفیگ خود را انتخاب کنید 👇🏻',
                'reply_markup': {
                    'inline_keyboard': usage_list
                },
            }
            cls.send_api("editMessageText", data)
        else:
            data3 = {
                'chat_id': chat_id,
                "text": "این سرویس حذف شده است و قابل تمدید نیست.",
                'message_id': msg_id,
            }
            cls.send_api("editMessageText", data3)

    @classmethod
    def tamdid_confirm_config_buying(cls, chat_id, *args):
        msg_id = int(args[0])
        arg_splited = args_spliter(args[1])
        if ConfigsInfo.objects.filter(config_uuid=arg_splited[0]).exists():
            config_info = ConfigsInfo.objects.get(config_uuid=arg_splited[0])
            expire_month = int(arg_splited[1])
            usage_limit = int(arg_splited[2])
            user_limit = int(arg_splited[3])
            custumer_obj = CustumerModel.objects.get(userid=chat_id)
            wallet_amount = custumer_obj.wallet
            price = PricesModel.objects.get(expire_limit=expire_month, user_limit=user_limit,
                                            usage_limit=usage_limit).price
            wallet_amount_text = f"{wallet_amount:,}"
            have_off_code = False
            text = ""

            pay_amount = price - wallet_amount
            price_text = f"{price:,}"
            pay_amount_text = f"{pay_amount:,}"

            if expire_month == 0:
                expire_month_text = " زمان نامحدود ♾"
                if UserActiveOffCodes.objects.filter(custumer__userid=chat_id, used=False, off_code__for_infinit_times=True).exists():
                    have_off_code = True
            else:
                expire_month_text = f" {expire_month} ماهه"
            if usage_limit == 0:
                usage_limit_text = ' نامحدود ♾'
                if UserActiveOffCodes.objects.filter(custumer__userid=chat_id, used=False,off_code__for_infinit_usages=True).exists():
                    have_off_code = True
            else:
                usage_limit_text = f'{usage_limit} GB'

            if user_limit == 0:
                user_limit_text = ' بدون محدودیت ♾'
            else:
                user_limit_text = user_limit
            server_name = config_info.server.server_name
            if usage_limit != 0 and expire_month != 0 and UserActiveOffCodes.objects.filter(custumer__userid=chat_id,
                                                                            used=False,off_code__for_not_infinity=True).exists():
                have_off_code = True

            if have_off_code:
                text = "🟢 کد تخفیف شما صورت گرفت و از هزینه سرویس کم گردید." "\n\n"
                off_model = UserActiveOffCodes.objects.get(custumer__userid=chat_id, used=False)
                if off_model.off_code.type_off:
                    price = price - int(off_model.off_code.amount * price / 100)
                else:
                    price = price - (off_model.off_code.amount * 1000)
            pay_amount = price - wallet_amount
            price_text = f"{price:,}"
            pay_amount_text = f"{pay_amount:,}"

            if wallet_amount >= price:

                data = {
                    'chat_id': chat_id,
                    'message_id': msg_id,
                    'text': text + f"♻️ تمدید سرویس: {config_info.config_name}" "\n\n" f' 🌍 سرور:  {server_name} \n' + f' ⏱ انقضا: {expire_month_text}\n'
                                                                                                                f' 🔃 حجم : {usage_limit_text} \n' + f' 👤 محدودیت کاربر: {user_limit_text}\n\n' + f' 💵 هزینه سرویس: {price_text} تومان \n\n'
                                                                                                                                                                                                 f'کاربر گرامی، موجودی کیف پول شما {wallet_amount_text} تومان است، برای فعال سازی این سرویس مبلغ {price_text}'
                            + f' تومان از کیف پول شما کسر خواهد شد.\n تایید تمدید 👇🏻',
                    'reply_markup': {
                        'inline_keyboard': [[{'text': '✅ تایید خرید 💳',
                                              'callback_data': f'tam_wallet<~>{config_info.config_uuid}<%>{expire_month}<%>{usage_limit}<%>{user_limit}'}],
                                            [{"text": '🔙 بازگشت',
                                              'callback_data': f"tamdid_expire_time<~>{config_info.config_uuid}<%>{expire_month}"}],
                                            [{'text': 'انصراف ❌', 'callback_data': 'abort_buying'}]]
                    },
                }
            else:
                if wallet_amount == 0:
                    text_pay = f'کاربر گرامی، برای تمدید این سرویس مبلغ {pay_amount_text}'
                else:
                    text_pay = f'کاربر گرامی، موجودی کیف پول شما {wallet_amount_text} تومان است، برای تمدید این سرویس مبلغ {pay_amount_text}'
                data = {
                    'chat_id': chat_id,
                    'message_id': msg_id,
                    'text':text + f"♻️ تمدید سرویس: {config_info.config_name}" "\n\n" f' 🌍 سرور:  {server_name} \n' + f' ⏱ انقضا: {expire_month_text}\n'
                                                                                                                f' 🔃 حجم : {usage_limit_text} \n' + f' 👤 محدودیت کاربر: {user_limit_text}\n\n' + f' 💵 هزینه سرویس: {price_text} تومان \n\n'
                            + text_pay + f' تومان را پرداخت کنید 👇🏻',
                    'reply_markup': {
                        'inline_keyboard': [[{'text': '✅ پرداخت / کارت به کارت 💳',
                                              'callback_data': f'tam_pay<~>{config_info.config_uuid}<%>{expire_month}<%>{usage_limit}<%>{user_limit}'}],
                                            [{"text": '🔙 بازگشت',
                                              'callback_data': f"tamdid_expire_time<~>{config_info.config_uuid}<%>{expire_month}"}],
                                            [{'text': 'انصراف ❌', 'callback_data': 'abort_buying'}]]
                    },
                }
            cls.send_api("editMessageText", data)
        else:
            data3 = {
                'chat_id': chat_id,
                "text": "این سرویس حذف شده است و قابل تمدید نیست.",
                'message_id': msg_id,
            }
            cls.send_api("editMessageText", data3)

    @classmethod
    def tamdid_pay_for_config(cls, chat_id, *args):
        msg_id = args[0]
        arg_splited = args_spliter(args[1])
        if ConfigsInfo.objects.filter(config_uuid=arg_splited[0]).exists():
            config_info = ConfigsInfo.objects.get(config_uuid=arg_splited[0])
            expire_limit = int(arg_splited[1])
            usage_limit = int(arg_splited[2])
            user_limit = int(arg_splited[3])
            price = PricesModel.objects.get(usage_limit=usage_limit, expire_limit=expire_limit,
                                            user_limit=user_limit).price
            with open(settings.BASE_DIR / 'settings.json', 'r') as f:
                data = json.load(f)
                card_num = data["pay_card_number"]
                card_name = data["pay_card_name"]
            data = {
                'message_id': msg_id,
                'chat_id': chat_id,
                'text': f" مبلغ {price - config_info.chat_id.wallet}تومان را به شماره کارت زیر انتقال دهید، سپس عکس آنرا بعد از همین پیام ارسال نمایید : " + f'\n\n`{card_num}`\n {card_name}',
                'parse_mode': 'Markdown',
            }
            data2 = {
                'chat_id': chat_id,
                "text": "تصویر پرداختی خود را ارسال کنید :",
                'resize_keyboard': True,
                'one_time_keyboard': True,
                'reply_markup': {
                    'keyboard': [
                        [{'text': '❌ لغو پرداخت 💳'}]]
                },
            }
            Customer.change_custimer_temp_status(chat_id, "get_paid_picture_for_tamdid")
            Paying.pay__tamdid__config_before_img(chat_id, price, config_info.config_uuid)
            Configs.add_configs_to__tamdid__queue_before_confirm(config_info.config_uuid, usage_limit,
                                                                 expire_limit * 30, user_limit, price)
            # expire limit * 30
            cls.send_api("sendMessage", data2)
            cls.send_api("editMessageText", data)
        else:
            data3 = {
                'chat_id': chat_id,
                "text": "این سرویس حذف شده است و قابل تمدید نیست.",
                'message_id': msg_id,
            }
            cls.send_api("editMessageText", data3)

    @classmethod
    def tamdid_config_from_wallet(cls, chat_id, *args):
        msg_id = int(args[0])
        arg_splited = args_spliter(args[1])
        if ConfigsInfo.objects.filter(config_uuid=arg_splited[0]).exists():
            config_info = ConfigsInfo.objects.get(config_uuid=arg_splited[0])
            expire_limit = int(arg_splited[1])
            usage_limit = int(arg_splited[2])
            user_limit = int(arg_splited[3])
            price = PricesModel.objects.get(usage_limit=usage_limit, expire_limit=expire_limit,
                                            user_limit=user_limit).price
            create_config = Configs.tamdid_config_from_wallet(arg_splited[0], expire_limit, usage_limit, user_limit,
                                                              price)
            if create_config:
                data = {
                    'message_id': msg_id,
                    'chat_id': chat_id,
                    'text': f"کانفیک شما تمدید شد و مبلغ {price} تومان از کیف پول شما کسر شد.",
                    'parse_mode': 'Markdown',
                }
                cls.send_api("editMessageText", data)
            else:
                msg = f'اتصال به سرور {ServerModel.objects.get(server_id=config_info.server.server_id).server_name} برقرار نشد.' '\nدقایقی دیگر دوباره امتحان کنید.'
                data = {
                    'message_id': msg_id,
                    'chat_id': chat_id,
                    'text': msg,
                    'parse_mode': 'Markdown',
                }
                cls.send_api("editMessageText", data)

    @classmethod
    def test_conf(cls, chat_id, *args):
        customer = CustumerModel.objects.get(userid=chat_id)
        if TestConfig.objects.filter(customer=customer).exists():
            cls.send_msg_to_user(chat_id, "کابر گرامی، شما تنها یکبار میتوانید کانفیگ تست دریافت کنید.")
        else:
            api = ServerApi.create_test_config(chat_id)
            if api:
                cls.send_msg_to_user(chat_id, api)
            else:
                cls.send_msg_to_user(chat_id,
                                     "در حال حاضر امکان دریافت کانفیگ تست نمی باشد، ساعاتی دیگر دوباره امتحان کنید.")

    @classmethod
    def invite_link(cls, chat_id, *args):
        cls.send_msg_to_user(chat_id, "این بخش موقتا غیرفعال است.")

    @classmethod
    def send_infinit_notification(cls, chat_id, iplimit, month):
        with open(settings.BASE_DIR / "settings.json", "r") as f:
            UNLIMIT_LIMIT = json.load(f)["unlimit_limit"]
            if (month in [1, 2, 3]) and (iplimit in [1, 2]):
                limit = UNLIMIT_LIMIT[f"{iplimit}u"][f"{month}m"]
            else:
                iplimit = max(1, min(iplimit, 2))
                month = max(1, min(month, 3))
                limit = UNLIMIT_LIMIT[f"{iplimit}u"][f"{month}m"]
            msg = "کاربر عزیز سرور نامحدود تقدیم شما ✔️" "\n\n" f"‼️ دقت کنید در صورت اتصال دستگاه بیش‌تر از تعداد کاربر تعیین شده برای کانفیگ ({iplimit} کاربره)، حتی برای یک اتصال، کانفیگ شما از حالت نامحدود به حالت حجمی  ({limit} گیگابایت) تبدیل می‌شود." "\n\n" "📌 لازم به ذکر است در صورت تبدیل حالت نامحدود به حجمی نه امکان عودت وجه و نه امکان بازگشت حالت کانفیگ فراهم نخواهد بود." "\n\n" "با تشکر از خرید شما ♥️"
            cls.send_msg_to_user(chat_id, msg)

    @classmethod
    def active_off_code(cls, chat_id, *args):
        off_uuid = args[0]
        if is_valid_uuid(off_uuid):
            if OffCodes.objects.filter(uid=off_uuid).exists():
                off_model = OffCodes.objects.get(uid=off_uuid)
                if off_model.end_timestamp > int(JalaliDateTime.now().timestamp()):
                    if UserActiveOffCodes.objects.filter(off_code=off_model, custumer__userid=chat_id).exists():
                        active_code_model = UserActiveOffCodes.objects.get(off_code=off_model, custumer__userid=chat_id)
                        if active_code_model.used and active_code_model.off_code.use_count == 1:
                            cls.send_msg_to_user(chat_id, "🔴 شما فقط یکبار میتوانید این کد تخفیف را فعال کنید.")
                        elif not active_code_model.used and active_code_model.off_code.use_count == 1:
                            cls.send_msg_to_user(chat_id,
                                                 "🟠 این کدتخفیف قبلا برای شما فعال شده است. دربخش پرداخت هزینه (خرید یا تمدید سرویس) بصورت خودکار برایتان محاسبه میگردد.")
                        elif active_code_model.used and active_code_model.off_code.use_count == 0:
                            if UserActiveOffCodes.objects.filter(custumer__userid=chat_id, used=False).exists():
                                obj = UserActiveOffCodes.objects.get(custumer__userid=chat_id, used=False)
                                obj.used = True
                                obj.save()
                            active_code_model.used = False
                            active_code_model.save()

                            cls.send_msg_to_user(chat_id, "🟢 این کدتخفیف دوباره برای شما فعال گردید.")
                        elif not active_code_model.used and active_code_model.off_code.use_count == 0:
                            cls.send_msg_to_user(chat_id,
                                                 "🟠 این کد از قبل برای شما فعال است.  دربخش پرداخت هزینه (خرید یا تمدید سرویس) بصورت خودکار برایتان محاسبه میگردد.")
                    else:
                        if UserActiveOffCodes.objects.filter(custumer__userid=chat_id, used=False).exists():
                            UserActiveOffCodes.objects.get(custumer__userid=chat_id, used=False).delete()
                        UserActiveOffCodes.objects.create(off_code=off_model,
                                                          custumer=CustumerModel.objects.get(userid=chat_id)).save()
                        cls.send_msg_to_user(chat_id,
                                             "🟢 کد تخفیف برای شما فعال گردید. هنگام خرید یا تمدید سرویس به صورت خودکار (در مرحله پرداخت) برای شما محاسبه میگردد.")

                else:
                    cls.send_msg_to_user(chat_id, "🔴 مهلت فعال کردن این کد تخفیف گذشته است.")
            else:
                cls.send_msg_to_user(chat_id, "🔴 کد تخفیفی با این مشخصات یافت نشد.")
        else:
            cls.send_msg_to_user(chat_id, "🔴 لینک کد تخفیف اشتباه است.")
