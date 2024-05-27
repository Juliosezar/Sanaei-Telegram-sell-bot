from os import environ
from finance.views import Wallet
from django.conf import settings
import requests
from custumers.views import Customer
import json
from custumers.models import Customer as CustumerModel
from servers.models import Server as ServerModel

TOKEN = environ.get('TelegramToken')
TELEGRAM_SERVER_URL = f"https://api.telegram.org/bot{TOKEN}/"

"""
    class CommandRunner:
    
    all respons commands in this class

"""


class CommandRunner:
    @classmethod
    def send_api(cls, api_method, data):
        url = TELEGRAM_SERVER_URL + api_method
        response = requests.post(url, json=data).json()
        print(response)
        return response

    @classmethod
    def send_notification(cls, chat_id, msg):
        data = {'chat_id': chat_id,
                'text': msg}
        cls.send_api("sendMessage", data)

    @classmethod
    def abort(cls, chat_id, *args):
        cls.send_notification(chat_id, "❌ عملیات لغو شد.❗️")
        cls.main_menu(chat_id)

    @classmethod
    def get_user_info(cls, chat_id, *args):
        data = {'chat_id': chat_id}
        info = CommandRunner.send_api("getChat", data)
        if "username" in info["result"]:
            username = info["result"]["username"]
        else:
            username = None

        if "first_name" in info["result"]:
            first_name = info["result"]["first_name"]
        else:
            first_name = None

        return {"username": username, "first_name": first_name}

    @classmethod
    def welcome(cls, chat_id, *args):
        cls.send_notification(chat_id, "به بات فروش NAPSV VPN خوش آمدید.")

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
                    [{'text': 'ثبت لینک 🔗'}, {'text': 'تست رایگان 🔥'}],
                    [{'text': 'سرویس های من 🧑‍💻'}, {'text': 'کیف پول 💰'}],
                    [{'text': 'تعرفه ها 💳'}, {'text': 'ارتباط با ما 👤'}],
                    [{'text': 'آیدی من 💎'}, {'text': 'لینک دعوت 📥'}],
                    [{'text': 'راهنمای اتصال 💡'}, {'text': 'دانلود اپلیکیشن 💻📱'}],
                ],
                'resize_keyboard': True,
                'one_time_keyboard': False,

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
                with open(settings.BASE_DIR / 'connection/settings.json', 'r') as f:
                    data = json.load(f)
                    card_num = data["pay_card_number"]
                    card_name = data["pay_card_name"]
                data = {
                    'chat_id': chat_id,
                    'text': f" مبلغ {amount}تومان را به شماره کارت زیر انتقال دهید، سپس عکس آنرا بعد از همین پیام ارسال نمایید : " + f'\n\n`{card_num}`\n {card_name}',
                    'parse_mode': 'Markdown',
                }
                Customer.change_custimer_temp_status(chat_id, "get_paid_picture")
                cls.send_api("sendMessage", data)
            else:
                print("not number")
                cls.send_notification(chat_id, "حداقل مقدار پرداختی 2000 تومان است. دوباره وارد کنید :")
        else:
            cls.send_notification(chat_id, "مقدار را به صورت لاتین(انگلیسی) و به تومان وارد کنید :")

    @classmethod
    def contact_us(cls, chat_id, *args):
        data = {
            'chat_id': chat_id,
            'text': f' با سلام خدمت شما کاربر گرامی \n\n' + "🟢 پشتیبانی ۲۴ ساعته با آی دی زیر    👇\n" + "🆔 @NapsV_supp"
        }
        cls.send_api("sendMessage", data)

    @classmethod
    def select_server(cls, chat_id, *args):
        server_obj = ServerModel.objects.filter(active=True)
        keyboard_list = []
        for i in server_obj:
            keyboard_list.append(
                [{'text':i.server_name, 'callback_data':f"server_buy<~>{i.server_username}"}]
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
    def select_config_expire_time(cls, chat_id, *args):
        print(args)
        msg_id = int(args[1])
        print(msg_id)
        data = {
            'chat_id': chat_id,
            'message_id' : msg_id,
            'text': '🌐 مدت زمان سرویس خود را انتخاب کنید 👇🏻',
            'reply_markup': {
                'inline_keyboard':[
                    [{'text': "1month", 'callback_data': f"expire_time<~>6546"}]
            ]
            },
        }
        cls.send_api("editMessageText", data)