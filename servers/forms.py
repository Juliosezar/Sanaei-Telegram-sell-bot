from django import forms
from finance.models import Prices as PriceModel
from django.core.exceptions import ValidationError
from .models import Server

class SearchForm(forms.Form):
    search = forms.CharField(max_length=20,widget=forms.TextInput(attrs={'placeholder': 'Search UUID or NAME'}))



class CreateConfigForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["type"].choices = self.type_limit()
    def type_limit(self):
        types = [('limited','حجمی')]
        if PriceModel.objects.filter(usage_limit=0).exists():
            types.append(('usage_unlimit', "حجم نامحدود"))
        if PriceModel.objects.filter(expire_limit=0).exists():
            types.append(('time_unlimit', "زمان نامحدود"))
        return types


    type = forms.ChoiceField(required=False,)
    usage_limit = forms.CharField(required=False, widget=forms.Select(choices=[]))
    days_limit = forms.CharField(required=False, widget=forms.Select(choices=[]))
    ip_limit = forms.CharField(required=False, widget=forms.Select(choices=[]))
    paid = forms.BooleanField(required=False, initial=True)
    def clean_usage_limit(self):
        return self.cleaned_data.get('usage_limit')
    def clean_days_limit(self):
        return self.cleaned_data.get('days_limit')
    def clean_ip_limit(self):
        return self.cleaned_data.get('ip_limit')



class ManualCreateConfigForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["type"].choices = self.type_limit()
    def type_limit(self):
        types = [('limited','حجمی')]
        if PriceModel.objects.filter(usage_limit=0).exists():
            types.append(('usage_unlimit', "حجم نامحدود"))
        if PriceModel.objects.filter(expire_limit=0).exists():
            types.append(('time_unlimit', "زمان نامحدود"))
        return types



    type = forms.ChoiceField(required=False)
    usage_limit = forms.IntegerField(required=False)
    days_limit = forms.IntegerField(required=False)
    ip_limit = forms.ChoiceField(required=False, choices=[(1,'1 کاربره'),(2,'2 کاربره'),(3,'3 کاربره')])
    price = forms.IntegerField(required=False)
    paid = forms.BooleanField(required=False, initial=True)

    def clean_price(self):
        price = self.cleaned_data['price']
        if price is None:
            raise ValidationError('قیمت را وارد کنید.')
        elif not 0 <= price < 1500:
            raise ValidationError('قیمت باید بین 0 تا 1500 هزار تومان باشد.')
        return price

    def clean(self):
        type = self.cleaned_data.get('type')
        usage_limit = self.cleaned_data.get('usage_limit')
        days_limit = self.cleaned_data.get('days_limit')
        if type == "limited":
            if usage_limit is None:
                raise ValidationError('حجم کانفیگ را وارد کنید.')
            elif not 1 < usage_limit < 1000:
                raise ValidationError('حجم کانفیگ باید بین 1 تا 1000 گیگ باشد.')
            if days_limit is None:
                raise ValidationError('مدت زمان کانفیگ را وارد کنید.')
            elif not 0 < days_limit < 13:
                raise ValidationError('مدت زمان کانفیگ باید بین 1 تا 12 ماه باشد.')
        elif type == 'usage_unlimit':
            if days_limit is None:
                raise ValidationError('مدت زمان کانفیگ را وارد کنید.')
            elif not 0 < days_limit < 13:
                raise ValidationError('مدت زمان کانفیگ باید بین 1 تا 12 ماه باشد.')
        elif type == 'time_unlimit':
            if usage_limit is None:
                raise ValidationError('حجم کانفیگ را وارد کنید.')
            elif not 1 < usage_limit < 1000:
                raise ValidationError('حجم کانفیگ باید بین 1 تا 1000 گیگ باشد.')



class ChangeConfigSettingForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.config_data = kwargs.pop('config_data', None)
        super().__init__(*args, **kwargs)
        if self.config_data:
            self.fields["usage_limit"].initial = self.config_data["usage"]
            self.fields["days_limit"].initial = self.config_data["expire_time"]
            self.fields["ip_limit"].initial = self.config_data["ip_limit"]

    usage_limit = forms.IntegerField(required=False)
    days_limit = forms.IntegerField(required=False)
    ip_limit = forms.IntegerField(required=False)

    def clean(self):
        usage_limit = self.cleaned_data.get('usage_limit')
        days_limit = self.cleaned_data.get('days_limit')
        ip_limit = self.cleaned_data.get("ip_limit")
        if usage_limit is None:
            raise ValidationError('حجم کانفیگ را وارد کنید.')
        elif not 0 <= usage_limit < 1000:
            raise ValidationError('حجم کانفیگ باید بین 1 تا 1000 گیگ باشد.')
        if days_limit is None:
            raise ValidationError('مدت زمان کانفیگ را وارد کنید.')
        elif not 0 <= days_limit < 181:
            raise ValidationError('مدت زمان کانفیگ باید بین 1 تا 180 روز باشد.')
        if not 0 <= ip_limit < 4:
            raise ValidationError('محدودیت آی پی باید بین 0 تا 3 باشد.')


class AddServerForm(forms.Form):
    server_id = forms.IntegerField(required=True)
    server_name = forms.CharField(max_length=30, required=True)
    server_url = forms.CharField(max_length=60, required=True)
    username = forms.CharField(max_length=30, required=True)
    password = forms.CharField(max_length=30, required=True)
    server_fake_domain = forms.CharField(max_length=40, required=True)
    inbound_id = forms.IntegerField(required=True)
    inbound_port = forms.IntegerField(required=True)
    active = forms.BooleanField(initial=True)

    def clean_server_url(self):
        url = self.cleaned_data['server_url']
        if not url.startswith('http') or not url.endswith("/") or "panel" in url:
            raise ValidationError("url اشتباه است.")
        return url


class EditServerForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.server_id = kwargs.pop('server_id', None)
        super().__init__(*args, **kwargs)
        server = Server.objects.get(server_id=self.server_id)
        self.fields["server_name"].initial = server.server_name
        self.fields["server_url"].initial = server.server_url
        self.fields["username"].initial = server.username
        self.fields["password"].initial = server.password
        self.fields["server_fake_domain"].initial = server.server_fake_domain
        self.fields["inbound_id"].initial = server.inbound_id
        self.fields["inbound_port"].initial = server.inbound_port
        self.fields["active"].initial = server.active

    server_name = forms.CharField(max_length=30, required=True)
    server_url = forms.CharField(max_length=60, required=True)
    username = forms.CharField(max_length=30, required=True)
    password = forms.CharField(max_length=30, required=True)
    server_fake_domain = forms.CharField(max_length=40, required=True)
    inbound_id = forms.IntegerField(required=True)
    inbound_port = forms.IntegerField(required=True)
    active = forms.BooleanField(initial=True)

    def clean_server_url(self):
        url = self.cleaned_data['server_url']
        if not url.startswith('http://') or not url.endswith("/") or "panel" in url:
            raise ValidationError("url اشتباه است.")
        return url


class ChangeConfigLocForm(forms.Form):
    server = forms.ChoiceField(choices=[(i.server_id, i.server_name) for i in Server.objects.all()])

    def clean_server(self):
        server = self.cleaned_data['server']
        return int(server)


