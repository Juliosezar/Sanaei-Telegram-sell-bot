from os import environ
from finance.views import Wallet
from django.conf import settings
import requests
from custumers.views import Customer
import json
from custumers.models import Customer as CustumerModel
from servers.models import Server as ServerModel
from finance.views import Prices
from finance.models import Prices as PricesModel
from finance.models import ConfirmPaymentQueue as ConfirmPaymentQueueModel
from finance.views import Paying
from django.conf import settings
from servers.views import Configs
from uuid import uuid4
from django.core.files.base import ContentFile
from django.core.files.base import ContentFile


TOKEN = environ.get('TelegramToken')
TELEGRAM_SERVER_URL = f"https://api.telegram.org/bot{TOKEN}/"


"""
    class CommandRunner:
    
    all respons commands in this class

"""

def args_spliter(args):
    return args.split("<%>")


class CommandRunner:
    @classmethod
    def test(cls, chat_id):
        Prices.get_expire_times()

    @classmethod
    def send_api(cls, api_method, data):
        url = TELEGRAM_SERVER_URL + api_method
        response = requests.post(url, json=data).json()
        print(response)
        return response

    @classmethod
    def download_photo(cls, file_id, chat_id ):
        file_info = requests.get(f"https://api.telegram.org/bot{TOKEN}/getFile?file_id={file_id}").json()["result"]
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info['file_path']}"
        img_data = requests.get(file_url).content
        user_obj = CustumerModel.objects.get(userid=chat_id)
        cpq_obj = ConfirmPaymentQueueModel.objects.get(userid=user_obj, status=0)
        cpq_obj.image.save(file_id+".jpg",ContentFile(img_data),save=False)
        cpq_obj.status = 1
        cpq_obj.save()

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
                    [{'text': 'خرید سرویس 🛍','callback_data':"kjhbjbk"}],
                    [{'text': 'ثبت لینک 🔗'}, {'text': 'تست رایگان 🔥'}],
                    [{'text': 'سرویس های من 🧑‍💻'}, {'text': 'کیف پول 💰'}],
                    [{'text': 'تعرفه ها 💳'}, {'text': 'ارتباط با ما 👤'}],
                    [{'text': 'آیدی من 💎'}, {'text': 'لینک دعوت 📥'}],
                    [{'text': 'راهنمای اتصال 💡'}, {'text': 'دانلود اپلیکیشن 💻📱'}],
                ],
                'resize_keyboard': True,
                'one_time_keyboard': True,
                'is_persistent':False,
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
                Paying.pay_to_wallet_before_img(chat_id, amount)
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
                [{'text':i.server_name, 'callback_data':f"server_buy<~>{i.server_id}"}]
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
        server_obj = ServerModel.objects.filter(active=True)
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
        month_list.append([{'text':'🔙 بازگشت', 'callback_data':f"back_to_servers<~>"}])
        server_name = ServerModel.objects.get(server_id=server_id).server_name
        data = {
            'chat_id': chat_id,
            'message_id' : msg_id,
            'text': f' 🌍 سرور: {server_name} \n\n' + '⏱ مدت زمان سرویس خود را انتخاب کنید 👇🏻',
            'reply_markup': {
                'inline_keyboard':month_list
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
                u_text =  " ♾ " + "نامحدود" + " - " + f"{u.user_limit} کاربره" + " - " + f"{u.price} تومان "
            else:
                u_text = " 🔘 " + f"{u.usage_limit} گیگ" + " - "  + f"{u.price} تومان "
            usage_list.append([{'text': u_text, 'callback_data': f"usage_limit<~>{server_id}<%>{expire_month}<%>{u.usage_limit}<%>{u.user_limit}"}])
        usage_list.append([{'text':'🔙 بازگشت', 'callback_data':f"back_to_select_expire_time<~>{server_id}"}])
        server_name = ServerModel.objects.get(server_id=server_id).server_name

        if expire_month == 0:
            choosen = " زمان نامحدود ♾ "
        else:
            choosen = f" {expire_month} ماهه"
        data = {
            'chat_id': chat_id,
            'message_id': msg_id,
            'text':f' 🌍 سرور:  {server_name} \n\n' + f' ⏱ انقضا: {choosen}\n\n'+ '🔃 حجم کانفیگ خود را انتخاب کنید 👇🏻',
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
        pay_amount = price - wallet_amount
        price_text = f"{price:,}"
        wallet_amount_text = f"{wallet_amount:,}"
        pay_amount_text = f"{pay_amount:,}"

        if expire_month == 0:
            expire_month_text = " زمان نامحدود ♾"
        else:
            expire_month_text = f" {expire_month} ماهه"
        if usage_limit == 0:
            usage_limit_text = ' نامحدود ♾'
        else:
            usage_limit_text = f'{usage_limit} GB'

        if user_limit == 0:
            user_limit_text = ' بدون محدودیت ♾'
        else:
            user_limit_text = user_limit
        server_name = ServerModel.objects.get(server_id=server_id).server_name

        if wallet_amount >= price:

            data = {
                'chat_id': chat_id,
                'message_id': msg_id,
                'text': f' 🌍 سرور:  {server_name} \n' + f' ⏱ انقضا: {expire_month_text}\n'
                        f' 🔃 حجم : {usage_limit_text} \n' + f' 👤 محدودیت کاربر: {user_limit_text}\n\n' + f' 💵 هزینه سرویس: {price_text} تومان \n\n'
                        f'کاربر گرامی، موجودی کیف پول شما {wallet_amount_text} تومان است، برای فعال سازی این سرویس مبلغ {price_text}'
                        + f' تومان از کیف پول شما کسر خواهد شد.\n تایید خرید 👇🏻',
                'reply_markup': {
                    'inline_keyboard': [[{'text': '✅ تایید خرید 💳', 'callback_data': f'config_buy_confirmed<~>{server_id}<%>{expire_month}<%>{usage_limit}<%>{user_limit}'}],
                                        [{"text": '🔙 بازگشت','callback_data': f"expire_time<~>{server_id}<%>{expire_month}"}],
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
                'text': f' 🌍 سرور:  {server_name} \n' + f' ⏱ انقضا: {expire_month_text}\n'
                        f' 🔃 حجم : {usage_limit_text} \n' + f' 👤 محدودیت کاربر: {user_limit_text}\n\n' + f' 💵 هزینه سرویس: {price_text} تومان \n\n'
                        + text_pay + f' تومان را پرداخت کنید 👇🏻',
                'reply_markup': {
                    'inline_keyboard': [[{'text':'✅ پرداخت / کارت به کارت 💳', 'callback_data':f'pay_for_config<~>{server_id}<%>{expire_month}<%>{usage_limit}<%>{user_limit}'}],
                                        [{"text":'🔙 بازگشت', 'callback_data':f"expire_time<~>{server_id}<%>{expire_month}"}],
                                        [{'text': 'انصراف ❌' , 'callback_data': 'abort_buying'}]]
                },
            }
            data2 = {

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
        price = PricesModel.objects.get(usage_limit=usage_limit,expire_limit=expire_limit, user_limit=user_limit).price
        print(args)
        with open(settings.BASE_DIR / 'connection/settings.json', 'r') as f:
            data = json.load(f)
            card_num = data["pay_card_number"]
            card_name = data["pay_card_name"]
        data = {
            'message_id': msg_id,
            'chat_id': chat_id,
            'text': f" مبلغ {price}تومان را به شماره کارت زیر انتقال دهید، سپس عکس آنرا بعد از همین پیام ارسال نمایید : " + f'\n\n`{card_num}`\n {card_name}',
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
        Configs.add_configs_to_queue_before_confirm(server_id, chat_id, uu_id, usage_limit, expire_limit, user_limit, price)

        cls.send_api("sendMessage", data2)
        cls.send_api("editMessageText", data)




