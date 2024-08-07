from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .command_runer import CommandRunner
from custumers.models import Customer as CustumerModel
from reports.models import ErrorLog
from persiantools.jdatetime import JalaliDateTime
import traceback
COMMANDS = {
    '/start': CommandRunner.main_menu,
    'خرید سرویس 🛍': CommandRunner.select_server,
    'back_to_servers': CommandRunner.back_to_select_server,
    'کیف پول 💰': CommandRunner.show_wallet_status,
    'تست رایگان 🔥': CommandRunner.test_conf,
    'سرویس های من 🧑‍💻': CommandRunner.my_services,
    'تعرفه ها 💳': CommandRunner.send_prices,
    'ارتباط با ادمین 👤': CommandRunner.contact_us,
    'آیدی من 🆔': CommandRunner.myid,
    # 'لینک دعوت 📥': CommandRunner.invite_link,
    'down_guid_app': CommandRunner.down_guid_app,
    '💻📱 دانلود اپلیکیشن و راهنمای اتصال 💡': CommandRunner.download_apps,
    "send_guid":CommandRunner.send_guid,
    'add_to_wallet': CommandRunner.set_pay_amount,
    'set_pay_amount': CommandRunner.send_pay_card_info,
    '❌ لغو پرداخت 💳': CommandRunner.abort,
    'server_buy': CommandRunner.select_config_expire_time,
    'expire_time': CommandRunner.select_config_usage,
    'usage_limit': CommandRunner.confirm_config_buying,
    'pay_for_config': CommandRunner.pay_for_config,
    'buy_config_from_wallet': CommandRunner.buy_config_from_wallet,
    'abort_buying': CommandRunner.abort_buying,
    'service_status': CommandRunner.get_service,
    'tamdid': CommandRunner.tamdid_select_config_expire_time,
    'tamdid_expire_time': CommandRunner.tamdid_select_config_usage,
    'tam_usage': CommandRunner.tamdid_confirm_config_buying,
    'tam_wallet': CommandRunner.tamdid_config_from_wallet,
    "tam_pay": CommandRunner.tamdid_pay_for_config,
    "choose_location": CommandRunner.choose_location,
    "change_location": CommandRunner.change_location,
    "confirm_change": CommandRunner.confirm_change,
    "QRcode": CommandRunner.Qrcode
}

'''
    webhook() function recieves bot commands from Telgram Servers
    with POST method and handle what command will run for respons
    to user.
'''


@csrf_exempt
def webhook(request):
    if request.method == 'POST':
        try:
            update = json.loads(request.body)
            if 'message' in update:
                chat_id = update['message']['chat']['id']
                if not CustumerModel.objects.filter(userid=chat_id).exists():
                    CommandRunner.main_menu(chat_id)
                if not CustumerModel.objects.get(userid=chat_id).active:
                    CommandRunner.send_msg_to_user(chat_id, "🚫 دسترسی شما به بات توسط ادمین لغو شده است.")
                    return JsonResponse({'status': 'ok'})
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
                        CommandRunner.send_msg_to_user(chat_id, "لطفا عکس پرداختی خود را ارسال نمایید :")
                    elif CustumerModel.objects.get(userid=chat_id).temp_status == "get_paid_picture_for_config":
                        CommandRunner.send_msg_to_user(chat_id, "لطفا عکس پرداختی خود را ارسال نمایید :")
                    elif CustumerModel.objects.get(userid=chat_id).temp_status == "get_paid_picture_for_tamdid":
                        CommandRunner.send_msg_to_user(chat_id, "لطفا عکس پرداختی خود را ارسال نمایید :")
                    elif "/start register_" in text:
                        CommandRunner.register_config(chat_id, text.replace("/start register_", ""))
                    elif "/start off_code_" in text:
                        CommandRunner.active_off_code(chat_id, text.replace("/start off_code_", ""))
                    else:
                        CommandRunner.send_msg_to_user(chat_id, "ورودی نامعتبر")
                        CommandRunner.main_menu(chat_id)

                elif "photo" in update["message"]:
                    if CustumerModel.objects.get(userid=chat_id).temp_status == "get_paid_picture":
                        photo = (update["message"]["photo"][-1])
                        file_id = photo["file_id"]
                        CommandRunner.download_photo(file_id, chat_id, False)
                        CommandRunner.send_msg_to_user(chat_id, "✅ تصویر شما دریافت شد.\n منتظر تایید پرداخت توسط همکاران ما باشید.\nپس از تایید مبلغ مورد نظر به کیف پولتان اضافه خواهد شد." "\n\n" "⭕️ لطفا از ارسال دوباره ی پرداخت خود، اکیدا خودداری کنید.")

                    elif CustumerModel.objects.get(userid=chat_id).temp_status == "get_paid_picture_for_config":
                        photo = (update["message"]["photo"][-1])
                        file_id = photo["file_id"]
                        CommandRunner.download_photo(file_id, chat_id, True)
                        CommandRunner.send_msg_to_user(chat_id, "✅ تصویر شما دریافت شد.\n منتظر تایید پرداخت توسط همکاران ما باشید.\nپس از تایید کانفیگ شما به صورت خودکار برایتان ارسال میگردد." "\n\n" "⭕️ لطفا از ارسال دوباره ی پرداخت خود، اکیدا خودداری کنید.")

                    elif CustumerModel.objects.get(userid=chat_id).temp_status == "get_paid_picture_for_tamdid":
                        photo = (update["message"]["photo"][-1])
                        file_id = photo["file_id"]
                        CommandRunner.download_photo(file_id, chat_id, True, True)
                        CommandRunner.send_msg_to_user(chat_id, "✅ تصویر شما دریافت شد.\n منتظر تایید پرداخت توسط همکاران ما باشید.\nپس از تایید کانفیگ شما به صورت خودکار تمدید میگردد و به شما اطلاع رسانی میشود." "\n\n" "⭕️ لطفا از ارسال دوباره ی پرداخت خود، اکیدا خودداری کنید.")


                    else:
                        CommandRunner.send_msg_to_user(chat_id, "ورودی نامعتبر")
                    COMMANDS["/start"](chat_id)

            elif 'callback_query' in update:
                msg_id = update["callback_query"]["message"]["message_id"]
                query_data = update['callback_query']['data']
                chat_id = update['callback_query']['message']['chat']['id']
                if not CustumerModel.objects.filter(userid=chat_id).exists():
                    CommandRunner.main_menu(chat_id)
                if not CustumerModel.objects.get(userid=chat_id).active:
                    CommandRunner.send_msg_to_user(chat_id, "🚫 دسترسی شما به بات توسط ادمین لغو شده است.")
                    return JsonResponse({'status': 'ok'})
                if query_data.split("<~>")[0] in COMMANDS.keys():
                    command = query_data.split("<~>")[0]
                    if "<~>" in query_data:
                        args = query_data.split("<~>")[1]
                        COMMANDS[command](chat_id, msg_id, args)
                    else:
                        COMMANDS[command](chat_id, msg_id)
                else:
                    CommandRunner.send_msg_to_user(chat_id, "ورودی نامعتبر")
                    COMMANDS["/start"](chat_id)
            return JsonResponse({'status': 'ok'})
        except Exception:
            error_str = traceback.format_exc()
            ErrorLog.objects.create(error=str(error_str), timestamp=int(JalaliDateTime.now().timestamp())).save()
            return JsonResponse({'status': 'Connection refused'})
    return JsonResponse({'status': 'not a POST request'})
