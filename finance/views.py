from django.shortcuts import render, redirect
from .models import Prices as PriceModel
# from .models import Payment
from custumers.models import Customer
from finance.models import ConfirmPaymentQueue as PaymentQueueModel
from finance.models import ConfirmTamdidPaymentQueue as TamdidPaymentQueueModel
from servers.models import CreateConfigQueue, ConfigsInfo
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from servers.views import ServerApi, Configs
from django.contrib import messages
from .forms import DenyForm, AddPriceForm, EditPriceForm


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
            config_price=price,
            pay_price=price - user_obj.wallet,
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
            config_price=None,
            pay_price=price,
            status=0,
        ).save()

    @classmethod
    def pay__tamdid__config_before_img(cls, user_id, price, uuid):
        config = ConfigsInfo.objects.get(config_uuid=uuid)
        user_obj = Customer.objects.get(userid=user_id)
        if TamdidPaymentQueueModel.objects.filter(config=config, status=0).exists():
            TamdidPaymentQueueModel.objects.get(config=config, status=0).delete()
        TamdidPaymentQueueModel.objects.create(
            config=config,
            config_price=price,
            pay_price=price - user_obj.wallet,
            status=0,
        ).save()


class ConfirmPaymentPage(LoginRequiredMixin, View):
    def get(self, request, show_box):
        pay_queue_obj = PaymentQueueModel.objects.filter(status=1)
        pay_tamdid_obj = TamdidPaymentQueueModel.objects.filter(status=1)
        second_pay_queue_obj = PaymentQueueModel.objects.filter(status=2)
        second_tamdid_pay_queue_obj = TamdidPaymentQueueModel.objects.filter(status=2)
        not_paid_obj = ConfigsInfo.objects.filter(paid=False)
        if not not_paid_obj.exists() and not pay_queue_obj.exists() and not second_pay_queue_obj.exists():
            messages.info(request, "پرداختی برای تایید نمانده است. \n برای اطمینان یکبار صفحه را رفرش کنید.")
        return render(request, 'confirm_payment.html',
                      {'confirm': pay_queue_obj, "confirm_count": pay_queue_obj.count() + pay_tamdid_obj.count(),
                       "second_confirm": second_pay_queue_obj, "second_confirm_count": second_pay_queue_obj.count() + second_tamdid_pay_queue_obj.count(),
                       "second_tamdid_pay": second_tamdid_pay_queue_obj,
                       "not_paid": not_paid_obj, "not_paid_count": not_paid_obj.count(),
                       "confirm_tamdid_pay": pay_tamdid_obj,"show_box": show_box})


class FirstConfirmPayment(LoginRequiredMixin, View):
    def get(self, request, obj_id):
        from connection.command_runer import CommandRunner
        model_obj = PaymentQueueModel.objects.get(id=obj_id)
        if model_obj.status == 1:
            Wallet.add_to_wallet(model_obj.custumer.userid, model_obj.pay_price)
            if model_obj.config_in_queue:
                if Customer.objects.get(userid=model_obj.custumer.userid).wallet >= model_obj.config_price:
                    CommandRunner.send_msg_to_user(model_obj.custumer.userid, "پرداخت شما تایید شد. ✅")
                    Configs.create_config_from_queue(config_uuid=model_obj.config_uuid)
                else:
                    CommandRunner.send_msg_to_user(model_obj.custumer.userid,
                                                   f'کابر گرامی مبلغ {model_obj.pay_price} تومان به کیف پول شما اضافه گردید. این مبلغ برای خرید کانفیک مورد نظر کافی نیست. ')
            else:
                Wallet.add_to_wallet(model_obj.custumer.userid, model_obj.pay_price)
                msg = 'پرداخت شما تایید و به کیف پول شما اضافه شد.'
                CommandRunner.send_msg_to_user(model_obj.custumer.userid, msg)
            model_obj.status = 2
            model_obj.save()
            messages.success(request, 'پرداخت با موفقیت تایید و به کاربر ارسال شد.')
        else:
            messages.error(request, "این پرداخت توسط ادمین دیگری تایید یا رد شده است.")
        return redirect('finance:confirm_payments', 1)


class SecondConfirmPayment(LoginRequiredMixin, View):
    def get(self, request, obj_id):
        from connection.command_runer import CommandRunner
        model_obj = PaymentQueueModel.objects.get(id=obj_id)
        if model_obj.status == 1:
            Wallet.add_to_wallet(model_obj.custumer.userid, model_obj.pay_price)
            if model_obj.config_in_queue:
                if Customer.objects.get(userid=model_obj.custumer.userid).wallet >= model_obj.config_price:
                    Configs.create_config_from_queue(config_uuid=model_obj.config_uuid)
                else:
                    CommandRunner.send_msg_to_user(model_obj.custumer.userid,
                                                   f'کابر گرامی مبلغ {model_obj.pay_price} تومان به کیف پول شما اضافه گردید. این مبلغ برای خرید کانفیک مورد نظر کافی نیست. ')
            else:
                Wallet.add_to_wallet(model_obj.custumer.userid, model_obj.pay_price)
                msg = 'پرداخت شما تایید و به کیف پول شما اضافه شد.'
                CommandRunner.send_msg_to_user(model_obj.custumer.userid, msg)
            model_obj.status = 3
            model_obj.save()
            messages.success(request, 'پرداخت با موفقیت تایید و به کاربر ارسال شد.')

        elif model_obj.status == 2:
            model_obj.status = 3
            model_obj.save()
            messages.success(request, 'پرداخت با موفقیت تایید شد.')
            return redirect('finance:confirm_payments', 2)
        # ToDO
        else:
            messages.error(request, "این پرداخت توسط ادمین دیگری تایید یا رد شده است.")
        return redirect('finance:confirm_payments', 2)


class FirstTamdidConfirmPayment(LoginRequiredMixin, View):
    def get(self, request, obj_id):
        from connection.command_runer import CommandRunner
        model_obj = TamdidPaymentQueueModel.objects.get(id=obj_id)
        if model_obj.status == 1:
            Wallet.add_to_wallet(model_obj.config.chat_id.userid, model_obj.pay_price)

            if Customer.objects.get(userid=model_obj.config.chat_id.userid).wallet >= model_obj.config_price:
                CommandRunner.send_msg_to_user(model_obj.config.chat_id.userid, "پرداخت شما تایید شد. ✅")
                Configs.tamdid_config_from_queue(config_uuid=model_obj.config.config_uuid)
            else:
                CommandRunner.send_msg_to_user(model_obj.config.chat_id.userid,
                                               f'کابر گرامی مبلغ {model_obj.pay_price} تومان به کیف پول شما اضافه گردید. این مبلغ برای تمدید سرویس مورد نظر کافی نیست. ')
            model_obj.status = 2
            model_obj.save()
            messages.success(request, 'پرداخت با موفقیت تایید و به کاربر ارسال شد.')
        else:
            messages.error(request, "این پرداخت توسط ادمین دیگری تایید یا رد شده است.")
        return redirect('finance:confirm_payments', 1)

class SecondTamdidConfirmPayment(LoginRequiredMixin, View):
    def get(self, request, obj_id):
        from connection.command_runer import CommandRunner
        model_obj = TamdidPaymentQueueModel.objects.get(id=obj_id)
        if model_obj.status == 1:
            Wallet.add_to_wallet(model_obj.config.chat_id.userid, model_obj.pay_price)

            if Customer.objects.get(userid=model_obj.config.chat_id.userid).wallet >= model_obj.config_price:
                Configs.tamdid_config_from_queue(config_uuid=model_obj.config.config_uuid)
            else:
                CommandRunner.send_msg_to_user(model_obj.config.chat_id.userid,
                                               f'کابر گرامی مبلغ {model_obj.pay_price} تومان به کیف پول شما اضافه گردید. این مبلغ برای تمدید سرویس مورد نظر کافی نیست. ')

            model_obj.status = 3
            model_obj.save()
            messages.success(request, 'پرداخت با موفقیت تایید و به کاربر ارسال شد.')

        elif model_obj.status == 2:
            model_obj.status = 3
            model_obj.save()
            messages.success(request, 'پرداخت با موفقیت تایید شد.')
            return redirect('finance:confirm_payments', 1)
        # ToDO
        else:
            messages.error(request, "این پرداخت توسط ادمین دیگری تایید یا رد شده است.")
        return redirect('finance:confirm_payments', 1)



class DenyPaymentPage(LoginRequiredMixin, View):
    def get(self, request, obj_id):
        model_obj = TamdidPaymentQueueModel.objects.get(id=obj_id)
        if model_obj.status != 1:
            messages.error(request, "این پرداخت توسط ادمین دیگری تایید یا رد شده است.")
            return redirect('finance:confirm_payments', 1)
        form = DenyForm()
        return render(request, 'deny_payment.html', {'obj': model_obj, 'form': form})

    def post(self, request, obj_id):
        from connection.command_runer import CommandRunner
        model_obj = TamdidPaymentQueueModel.objects.get(id=obj_id)
        form = DenyForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            if model_obj.status == 1:
                msg = "🔴 درخواست پرداخت شما رد شد." '\n' "✍🏻 علت : " f'{cd['reason']}' '\n\n'
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
                CommandRunner.send_msg_to_user(model_obj.config.chat_id.userid, msg)
                model_obj.status = 10
                model_obj.save()
                messages.success(request, "پرداخت با موفقیت رد تایید شد.")
                return redirect('finance:confirm_payments', 1)

            else:
                messages.error(request, "این پرداخت توسط ادمین دیگری تایید یا رد شده است.")
                return redirect('finance:confirm_payments', 1)
        return render(request, 'deny_payment.html', {'obj': model_obj, 'form': form})


class DenyPaymentAfterFirsConfirmPage(LoginRequiredMixin, View):
    def get(self, request, obj_id):
        model_obj = PaymentQueueModel.objects.get(id=obj_id)
        if model_obj.status != 2:
            messages.error(request, "این پرداخت توسط ادمین دیگری تایید یا رد شده است.")
            return redirect('finance:confirm_payments', 2)
        form = DenyForm()
        return render(request, 'deny_payment.html', {'obj': model_obj, 'form': form})

    def post(self, request, obj_id):
        from connection.command_runer import CommandRunner
        model_obj = PaymentQueueModel.objects.get(id=obj_id)
        form = DenyForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            if model_obj.status == 2:
                msg = "🔴 درخواست پرداخت شما رد شد." '\n' "✍🏻 علت : " f'{cd['reason']}' '\n\n'

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
                CommandRunner.send_msg_to_user(model_obj.custumer.userid, msg)
                model_obj.status = 10
                model_obj.save()
                messages.success(request, "پرداخت با موفقیت رد تایید شد.")
                return redirect('finance:confirm_payments', 2)

            else:
                messages.error(request, "این پرداخت توسط ادمین دیگری تایید یا رد شده است.")
                return redirect('finance:confirm_payments', 2)
        return render(request, 'deny_payment.html', {'obj': model_obj, 'form': form})


class DenyTamdidPaymentAfterFirsConfirmPage(LoginRequiredMixin, View):
    def get(self, request, obj_id):
        model_obj = TamdidPaymentQueueModel.objects.get(id=obj_id)
        if model_obj.status != 2:
            messages.error(request, "این پرداخت توسط ادمین دیگری تایید یا رد شده است.")
            return redirect('finance:confirm_payments', 2)
        form = DenyForm()
        return render(request, 'deny_payment.html', {'obj': model_obj, 'form': form})

    def post(self, request, obj_id):
        from connection.command_runer import CommandRunner
        model_obj = TamdidPaymentQueueModel.objects.get(id=obj_id)
        form = DenyForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            if model_obj.status == 2:
                msg = "🔴 درخواست پرداخت شما رد شد." '\n' "✍🏻 علت : " f'{cd['reason']}' '\n\n'

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
                CommandRunner.send_msg_to_user(model_obj.config.chat_id.userid, msg)
                model_obj.status = 10
                model_obj.save()
                messages.success(request, "پرداخت با موفقیت رد تایید شد.")
                return redirect('finance:confirm_payments', 2)


            else:
                messages.error(request, "این پرداخت توسط ادمین دیگری تایید یا رد شده است.")
                return redirect('finance:confirm_payments', 2)


class EditPricePayment(LoginRequiredMixin, View):
    def get(self, request, obj_id):
        form = EditPriceForm
        model_obj = PaymentQueueModel.objects.get(id=obj_id)
        return render(request, 'edit_price_payment.html', {'obj': model_obj, 'form': form})

    def post(self, request, obj_id):
        form = EditPriceForm(request.POST)
        model_obj = PaymentQueueModel.objects.get(id=obj_id)
        if form.is_valid():
            price = form.cleaned_data['price']
            model_obj.pay_price = price
            model_obj.save()
            messages.success(request, "مبلغ با موفقیت تغییر کرد. از لیست زیر آن را تایید کنید.")
            return redirect('finance:confirm_payments', 1)
        return render(request, 'edit_price_payment.html', {'obj': model_obj, 'form': form})


class PayedAfterCreate(LoginRequiredMixin, View):
    def get(self, request, obj_id):
        try:
            model_obj = ConfigsInfo.objects.get(id=obj_id)
            model_obj.paid = True
            model_obj.save()
            messages.success(request, "پرداخت تایید شد.")
            # TODO: if config disabled ,enable it
        except:
            messages.error(request, "ارور در تایید پرداخت.")
        return redirect("finance:confirm_payments", 3)


class ShowPrices(LoginRequiredMixin, View):
    def get(self, request):
        price_model = PriceModel.objects.all().order_by('expire_limit', 'usage_limit')
        return render(request, 'show_prices.html', {'price_model': price_model})


class DeleteOrEditPrice(LoginRequiredMixin, View):
    def get(self, request, obj_id, action):
        model_obj = PriceModel.objects.get(id=obj_id)
        if action == "delete":
            model_obj.delete()
            messages.success(request, "تعرفه با موفقیت حذف شد.")
            return redirect('finance:show_prices')
        elif action == "edit":
            return redirect('finance:show_prices')


# TODO

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
                ip_limit = 0
            price = cd["price"] * 1000

            PriceModel.objects.create(
                price=price,
                expire_limit=int(month),
                user_limit=int(ip_limit),
                usage_limit=int(usage),
            ).save()
            return redirect('finance:show_prices')
        return render(request, 'AddPrice.html', {'form': form})
