from django import forms
from servers.models import Server

def server_list():
    return [(s.server_id, s.server_name) for s in Server.objects.all()]
class SendMessageForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea, required=True)
    all_user = forms.BooleanField(initial=True, required=False)
    server = forms.MultipleChoiceField(required=False,widget=forms.CheckboxSelectMultiple, choices=server_list())
