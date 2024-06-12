from django import forms
from finance.models import Prices as PriceModel
from django.core.exceptions import ValidationError


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
    paid = forms.BooleanField(required=False, initial=False)
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
    paid = forms.BooleanField(required=False, initial=False)

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
            print("working")
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
