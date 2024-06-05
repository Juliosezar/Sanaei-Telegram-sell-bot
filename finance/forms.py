from django import forms


class DenyForm(forms.Form):
    reason = forms.CharField(widget=forms.Textarea, max_length=100)
    delete_all_configs = forms.BooleanField(required=False)
    disable_all_configs = forms.BooleanField(required=False)
    ban_user = forms.BooleanField(required=False)
