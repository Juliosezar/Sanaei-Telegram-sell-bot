from django import forms
from servers.models import Server

def server_list():
    return [(s.server_id, s.server_name) for s in Server.objects.all()]
class SendMessageToAllForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea, required=True)
    all_user = forms.BooleanField(initial=True, required=False, label="All users")
    server = forms.MultipleChoiceField(required=False,widget=forms.CheckboxSelectMultiple, choices=server_list())

    def clean_message(self):
        message = self.cleaned_data['message']
        if len(message) < 2:
            raise forms.ValidationError("Message is too short")
        return message

class SendMessageToCustomerForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea, required=True)


