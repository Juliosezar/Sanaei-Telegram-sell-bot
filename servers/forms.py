from django import forms

class SearchForm(forms.Form):
    search = forms.CharField(max_length=20,widget=forms.TextInput(attrs={'placeholder': 'Search UUID or NAME'}))