from django.shortcuts import render, redirect
from .models import Prices as PriceModel
# from .models import Payment
from custumers.models import Customer
from finance.models import ConfirmPaymentQueue as PaymentQueueModel
from servers.models import CreateConfigQueue
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from servers.views import ServerApi, Configs
from django.contrib import messages
from .forms import DenyForm, AddPriceForm


class Wallet:
    @classmethod
    def get_wallet_anount(cls, user_id):
        amount = Customer.objects.get(userid=user_id).wallet
        return amount

    @classmethod
    def add_to_wallet(cls, user_id, amount):
        wallet_obj = Customer.objects.get(userid=user_id)
        wallet_obj.wallet = wallet_obj.wallet + amount
        wallet_obj.save()


class Prices:
    @classmethod
    def get_expire_times(cls):
        price_obj = PriceModel.objects.all()
        months = [m.expire_limit for m in price_obj]
        months = list(set(months))  # for delete same values
        return months

    @classmethod
    def get_usage_and_prices_of_selected_month(cls, month):
        price_obj = PriceModel.objects.filter(expire_limit=month)
        return price_obj


class Paying:
    @classmethod
    def pay_config_before_img(cls, user_id, price, uuid):
        user_obj = Customer.objects.get(userid=user_id)
        if PaymentQueueModel.objects.filter(custumer=user_obj, status=0).exists():
            PaymentQueueModel.objects.get(custumer=user_obj, status=0).delete()
        PaymentQueueModel.objects.create(
            custumer=user_obj,
            price=price,
            status=0,
            config_in_queue=True,
            config_uuid=uuid,
        ).save()

    @classmethod
    def pay_to_wallet_before_img(cls, user_id, price):
        user_obj = Customer.objects.get(userid=user_id)
        if PaymentQueueModel.objects.filter(custumer=user_obj, status=0).exists():
            PaymentQueueModel.objects.get(custumer=user_obj, status=0).delete()
        PaymentQueueModel.objects.create(
            custumer=user_obj,
            price=price,
            status=0,
            config_in_queue=False,
        ).save()


class ConfirmPaymentPage(LoginRequiredMixin, View):
    def get(self, request):
        pay_queue_obj = PaymentQueueModel.objects.filter(status=1)
        if not pay_queue_obj.exists():
            messages.info(request, "پرداختی برای تایید نمانده است. \n برای اطمینان یکبار صفحه را رفرش کنید.")
        return render(request, 'confirm_payment.html', {'obj': pay_queue_obj})


class FirstConfirmPayment(LoginRequiredMixin, View):
    def get(self, request, obj_id):
        from connection.command_runer import CommandRunner
        model_obj = PaymentQueueModel.objects.get(id=obj_id)
        if model_obj.status == 1:
            Wallet.add_to_wallet(model_obj.custumer.userid, model_obj.price)
            if model_obj.config_in_queue:
                if Customer.objects.get(userid=model_obj.custumer.userid).wallet >= model_obj.price:
                    CommandRunner.send_notification(model_obj.custumer.userid, "پرداخت شما تایید شد. ✅")
                    Configs.create_config_from_queue(config_uuid=model_obj.config_uuid)
                else:
                    CommandRunner.send_notification(model_obj.custumer.userid,
                                                    f'کابر گرامی مبلغ {model_obj.price} تومان به کیف پول شما اضافه گردید. این مبلغ برای خرید کانفیک مورد نظر کافی نیست. ')
            else:
                Wallet.add_to_wallet(model_obj.custumer.userid, model_obj.price)
                msg = 'پرداخت شما تایید و به کیف پول شما اضافه شد.'
                CommandRunner.send_notification(model_obj.custumer.userid, msg)
            model_obj.status = 2
            model_obj.save()
            messages.success(request, 'پرداخت با موفقیت تایید و به کاربر ارسال شد.')
        else:
            messages.error(request, "این پرداخت توسط ادمین دیگری تایید یا رد شده است.")
        return redirect('finance:confirm_payments')


class SecondConfirmPayment(LoginRequiredMixin, View):
    def get(self, request, obj_id):
        from connection.command_runer import CommandRunner
        model_obj = PaymentQueueModel.objects.get(id=obj_id)
        if model_obj.status == 1:
            Wallet.add_to_wallet(model_obj.custumer.userid, model_obj.price)
            if model_obj.config_in_queue:
                if Customer.objects.get(userid=model_obj.custumer.userid).wallet >= model_obj.price:
                    Configs.create_config_from_queue(config_uuid=model_obj.config_uuid)
                else:
                    CommandRunner.send_notification(model_obj.custumer.userid,
                                                    f'کابر گرامی مبلغ {model_obj.price} تومان به کیف پول شما اضافه گردید. این مبلغ برای خرید کانفیک مورد نظر کافی نیست. ')
            else:
                Wallet.add_to_wallet(model_obj.custumer.userid, model_obj.price)
                msg = 'پرداخت شما تایید و به کیف پول شما اضافه شد.'
                CommandRunner.send_notification(model_obj.custumer.userid, msg)
            model_obj.status = 2
            model_obj.save()
            messages.success(request, 'پرداخت با موفقیت تایید و به کاربر ارسال شد.')

        elif model_obj.status == 2:
            pass
        # ToDO
        else:
            messages.error(request, "این پرداخت توسط ادمین دیگری تایید یا رد شده است.")
        return redirect('finance:confirm_payments')


class DenyPaymentPage(LoginRequiredMixin, View):
    def get(self, request, obj_id):
        model_obj = PaymentQueueModel.objects.get(id=obj_id)
        if model_obj.status != 1:
            messages.error(request, "این پرداخت توسط ادمین دیگری تایید یا رد شده است.")
            return redirect('finance:confirm_payments')
        form = DenyForm()
        return render(request, 'deny_payment.html', {'obj': model_obj, 'form': form})

    def post(self, request, obj_id):
        from connection.command_runer import CommandRunner
        model_obj = PaymentQueueModel.objects.get(id=obj_id)
        form = DenyForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            if model_obj.status == 1:
                msg = "🔴 درخواست پرداخت شما رد شد." '\n' "✍🏻 علت : " f'{cd['reason']}' '\n\n'
                if model_obj.config_in_queue:
                    CreateConfigQueue.objects.get(config_uuid=model_obj.config_uuid).delete()
                    model_obj.config_in_queue = False

                if cd['delete_all_configs']:
                    msg = msg + "🚫 به دلیل تخلف کانفیگ های شما حذف شده است."
                else:
                    if cd['disable_all_configs']:
                        msg = msg + '\n' "🚫 به دلیل تخلف کانفیگ های شما غیرفعال شده است."
                    # TODO
                # TODO

                if cd['ban_user']:
                    msg = msg + '\n' "🚫 به دلیل تخلف شما بن شده و از استفاده از بات محروم میشوید."
                # TODO
                CommandRunner.send_notification(model_obj.custumer.userid, msg)
                model_obj.status = 10
                model_obj.save()
                messages.success(request, "پرداخت با موفقیت رد تایید شد.")
                return redirect('finance:confirm_payments')


            else:
                messages.error(request, "این پرداخت توسط ادمین دیگری تایید یا رد شده است.")
                return redirect('finance:confirm_payments')


class ShowPrices(LoginRequiredMixin, View):
    def get(self, request):
        price_model = PriceModel.objects.all().order_by('expire_limit', 'usage_limit')
        return render(request, 'show_prices.html', {'price_model': price_model})

class DeleteOrEditPrice(LoginRequiredMixin, View):
    def get(self, request, obj_id, action):
        model_obj = PriceModel.objects.get(id=obj_id)
        print(action)
        if action == "delete":
            print(1111)
            model_obj.delete()
            messages.success(request, "تعرفه با موفقیت حذف شد.")
            return redirect('finance:show_prices')
        elif action == "edit":
            return render(request,)

class AddPrice(LoginRequiredMixin, View):
    def get(self, request):
        form = AddPriceForm()
        return render(request, 'AddPrice.html', {'form': form})

    def post(self, request):
        form = AddPriceForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            if cd["type_conf"] == "limited":
                usage = cd["usage"]
                month = cd["month"]
                ip_limit = 0
            elif cd["type_conf"] == "inf_usage":
                usage = 0
                month = cd['month']
                ip_limit = cd["ip_limit"]
            elif cd["type_conf"] == "inf_time":
                usage = cd["usage"]
                month = 0
                ip_limit = cd["ip_limit"]
            price = cd["price"]


            PriceModel.objects.create(
                price=price,
                expire_limit=int(month),
                user_limit=int(ip_limit),
                usage_limit=int(usage),
            ).save()
            return redirect('finance:show_prices')
        return render(request, 'AddPrice.html', {'form': form})