from os import environ

TOKEN = environ.get('TelegramToken')
TELEGRAM_SERVER_URL = f"https://api.telegram.org/bot{TOKEN}/"
import requests

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


    @staticmethod
    def get_user_info(chat_id, args):
        data = {'chat_id': chat_id}
        CommandRunner.send_api("getChat", data)

    @staticmethod
    def main_menu(chat_id, args):
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
        CommandRunner.send_api("sendMessage", data)

    @staticmethod
    def buy_choose_server(chat_id, args):
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
        CommandRunner.send_api("sendMessage", data)
