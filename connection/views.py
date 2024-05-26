from os import environ
from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .command_runer import CommandRunner




COMMANDS = {
    "/start": CommandRunner.main_menu,
    'خرید سرویس 🛍': CommandRunner.buy_choose_server,
}

@csrf_exempt
def webhook(request):
    if request.method == 'POST':
        update = json.loads(request.body)
        if 'message' in update:
            chat_id = update['message']['chat']['id']
            print(update)
            if "text" in update["message"]:
                text = update['message']['text']
                if text in COMMANDS.keys():
                    command = text.split("<~>")[0]
                    if "<~>" in text:
                        args = text.split("<~>")[1]
                    else:
                        args = False
                    COMMANDS[command](chat_id,args)
            elif "photo" in update["message"]:
                print(update["message"]["photo"])
                text = False
            else:
                text = False
        elif 'callback_query' in update:
            query_id = update['callback_query']['id']
            query_data = update['callback_query']['data']
            chat_id = update['callback_query']['message']['chat']['id']
            print(query_data)
            


        else:
            print("not found")

        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'not a POST request'})
