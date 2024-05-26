from os import environ
from finance.views import Wallet

TOKEN = environ.get('TelegramToken')
TELEGRAM_SERVER_URL = f"https://api.telegram.org/bot{TOKEN}/"
import requests
from custumers.views import Customer

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
    def get_user_info(cls,chat_id, *args):
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
        data = {'chat_id': chat_id,
                'text':"به بات فروش NAPSV VPN خوش آمدید."
                }
        cls.send_api(chat_id, data)

    @classmethod
    def main_menu(cls, chat_id, *args):
        user_info = CommandRunner.get_user_info(chat_id)

        if not Customer.check_custumer_info(chat_id, user_info["first_name"], user_info["username"]):
            cls.welcome(chat_id)
        data = {
            'chat_id': chat_id,
            'text': '🏠 منوی اصلی 🏠.',
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
                'one_time_keyboard': True,
            }
        }
        cls.send_api("sendMessage", data)

    @classmethod
    def buy_choose_server(cls, chat_id, *args):
        data = {
            'chat_id': chat_id,
            'text': 'Choose an option:',
            'reply_markup': {
                'inline_keyboard': [
                    [{'text': 'Button 1', 'callback_data': 'server<~>12'}],
                    [{'text': 'Button 2', "callback_data": "server<~>14"}]
                ]
            }
        }
        cls.send_api("sendMessage", data)

    @classmethod
    def show_wallet_status(cls, chat_id, *args):
        # amount = Wallet.get_wallet_anount(chat_id)
        amount = 12
        data = {
            'chat_id': chat_id,
            'text': f'موجودی کیف پول شما : {amount}',
            'reply_markup': {
                'inline_keyboard': [
                    [{'text': 'Button 1', 'callback_data': 'server<~>12'}],
                    [{'text': 'Button 2', "callback_data": "server<~>14"}]
                ]
            }
        }
        cls.send_api("sendMessage", data)
