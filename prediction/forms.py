from django import forms

class PredictionForm(forms.Form):
    lat = forms.FloatField(label='lat')
    lon = forms.FloatField(label='lon')
    address = forms.CharField(label='address',max_length=255)
    place_name = forms.CharField(label='place name', max_length=255)
    date = forms.DateField(label='date', widget=forms.DateInput(attrs={'type': 'date'}))
