from django import forms
from .models import Annotator

import logging
log = logging.getLogger(__name__)

class AnnotatorForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AnnotatorForm, self).__init__(*args, **kwargs)

    def clean_power(self):
        value = self.cleaned_data['power']

        if int(value) < 0:
            raise forms.ValidationError('User Power should be a positive number')

        return value

    class Meta:
        model = Annotator
        fields = ('power',)

        widgets = {
            'power': forms.NumberInput(attrs={'min':1}),
        }

        labels = {
            'power': 'User Power',
        }