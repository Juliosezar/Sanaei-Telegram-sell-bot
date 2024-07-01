from django import forms
from django.core.exceptions import ValidationError
from finance.models import Prices as Prices_Model


class DenyForm(forms.Form):
    reason = forms.CharField(widget=forms.Textarea, max_length=100)
    delete_all_configs = forms.BooleanField(required=False)
    disable_all_configs = forms.BooleanField(required=False)
    ban_user = forms.BooleanField(required=False)




class AddPriceForm(forms.Form):
    type_conf = forms.ChoiceField(choices=[("limited", "حجمی"), ("inf_usage", "حجم نامحدود"), ("inf_time", "زمان نامحدود")])
    usage = forms.IntegerField(initial=0)
    month = forms.ChoiceField(choices=[(1,"1 ماه"),(2,"2 ماه"),(3,"3 ماه"),(6,"6 ماه")])
    ip_limit = forms.ChoiceField(choices=[(1,"1 کاربره"),(2,"2 کاربره")])
    price = forms.IntegerField(required=True)

    def clean(self):
        price = self.cleaned_data.get('price')
        usage = self.cleaned_data.get('usage')
        type_conf = self.cleaned_data.get('type_conf')
        ip_limit = self.cleaned_data.get('ip_limit')
        month = self.cleaned_data.get('month')
        if price:
            if not 10 < price < 999 :
                raise ValidationError('قیمت باید بین 10 تا 999 هزار تومان باشد.')
        else:
            raise ValidationError("قیمت را وارد کنید.")
        if type_conf == "limited" or type_conf == 'inf_time':
            if not 2 < usage < 900:
                raise ValidationError("حجم کانفیگ باید بین 2 تا 900 گیگ باشد.")

        if type_conf == "limited":
            ip_limit = 0
        elif type_conf == "inf_usage":
            usage = 0
        elif type_conf == "inf_time":
            month = 0
        if Prices_Model.objects.filter(
                user_limit=int(ip_limit),
                usage_limit=int(usage),
                expire_limit=int(month)).exists():
            raise ValidationError("این تعرفه قبلا ثبت شده است.")

class EditPriceForm(forms.Form):
    price = forms.IntegerField(required=True,widget=forms.TextInput(attrs={'placeholder': 'قیمت جدید / هزارتومان'}))
    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price:
            if not 5 < price < 999:
                raise ValidationError('قیمت باید بین 5 تا 999 هزار تومان باشد.')
        else:
            raise ValidationError("قیمت را وارد کنید.")
        return price * 1000
