from os import environ
from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .command_runer import CommandRunner
from custumers.models import Customer as CustumerModel
from servers.views import ServerApi
COMMANDS = {
    "/test": ServerApi.create_config,


    #########################
    '/start': CommandRunner.main_menu,
    'خرید سرویس 🛍': CommandRunner.select_server,
    'back_to_servers': CommandRunner.back_to_select_server,
    'کیف پول 💰': CommandRunner.show_wallet_status,
    'ثبت لینک 🔗': None,
    'تست رایگان 🔥': None,
    'سرویس های من 🧑‍💻': None,
    'تعرفه ها 💳': None,
    'ارتباط با ما 👤': CommandRunner.contact_us,
    'آیدی من 💎': None,
    'لینک دعوت 📥': None,
    'راهنمای اتصال 💡': None,
    'دانلود اپلیکیشن 💻📱': None,
    'add_to_wallet': CommandRunner.set_pay_amount,
    'set_pay_amount': CommandRunner.send_pay_card_info,
    '❌ لغو پرداخت 💳': CommandRunner.abort,
    'server_buy': CommandRunner.select_config_expire_time,
    'expire_time': CommandRunner.select_config_usage,
    'back_to_select_expire_time': CommandRunner.select_config_expire_time,
    'usage_limit': CommandRunner.confirm_config_buying,
    'pay_for_config': CommandRunner.pay_for_config,
}

'''
    webhook() function recieves bot commands from Telgram Servers
    with POST method and handle what command will run for respons
    to user.
'''


@csrf_exempt
def webhook(request):

    if request.method == 'POST':
        # try:
            update = json.loads(request.body)
            if 'message' in update:
                chat_id = update['message']['chat']['id']
                if not CustumerModel.objects.filter(userid=chat_id).exists():
                    CommandRunner.main_menu(chat_id)
                if "text" in update["message"]:
                    text = update['message']['text']
                    if text.split("<~>")[0] in COMMANDS.keys():
                        command = text.split("<~>")[0]
                        if "<~>" in text:
                            args = text.split("<~>")[1]
                            COMMANDS[command](chat_id, args)
                        else:
                            COMMANDS[command](chat_id)
                    elif CustumerModel.objects.get(userid=chat_id).temp_status == "set_pay_amount":
                        CommandRunner.send_pay_card_info(chat_id, text)
                    elif CustumerModel.objects.get(userid=chat_id).temp_status == "get_paid_picture":
                        CommandRunner.send_notification(chat_id, "لطفا عکس پرداختی خود را ارسال نمایید :")
                    elif CustumerModel.objects.get(userid=chat_id).temp_status == "get_paid_picture_for_config":
                        CommandRunner.send_notification(chat_id, "لطفا عکس پرداختی خود را ارسال نمایید :")
                    else:
                        CommandRunner.send_notification(chat_id,"ورودی نامعتبر")
                        CommandRunner.main_menu(chat_id)

                elif "photo" in update["message"]:
                    if CustumerModel.objects.get(userid=chat_id).temp_status == "get_paid_picture":
                        photo = (update["message"]["photo"][-1])
                        print(photo)
                        file_id = photo["file_id"]
                        CommandRunner.download_photo(file_id, chat_id)
                        CommandRunner.send_notification(chat_id, "تصویر شما دریافت شد.\n منتظر تایید پرداخت توسط همکاران ما باشید.\nپس از تایید مبلغ مورد نظر به کیف پولتان اضافه خواهد شد.")

                    elif CustumerModel.objects.get(userid=chat_id).temp_status == "get_paid_picture_for_config":
                        photo = (update["message"]["photo"][-1])
                        print(photo)
                        file_id = photo["file_id"]
                        CommandRunner.download_photo(file_id, chat_id)
                        CommandRunner.send_notification(chat_id, "تصویر شما دریافت شد.\n منتظر تایید پرداخت توسط همکاران ما باشید.\nپس از تایید کانفیگ شما به صورت خودکار برایتان ارسال میگردد.")
                    else:
                        CommandRunner.send_notification(chat_id, "ورودی نامعتبر")
                    COMMANDS["/start"](chat_id)

            elif 'callback_query' in update:
                msg_id = update["callback_query"]["message"]["message_id"]
                print(update)
                query_data = update['callback_query']['data']
                chat_id = update['callback_query']['message']['chat']['id']
                if query_data.split("<~>")[0] in COMMANDS.keys():
                    command = query_data.split("<~>")[0]
                    if "<~>" in query_data:
                        args = query_data.split("<~>")[1]
                        COMMANDS[command](chat_id, msg_id, args)
                    else:
                        COMMANDS[command](chat_id, msg_id)
                else:
                    CommandRunner.send_notification(chat_id, "ورودی نامعتبر")
                    COMMANDS["/start"](chat_id)
            return JsonResponse({'status': 'ok'})
        # except Exception as e:
        #     print(e)
    return JsonResponse({'status': 'not a POST request'})
