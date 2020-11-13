import re
from django.conf import settings
from django.shortcuts import resolve_url
from django import forms
from django.forms import Form, ModelForm, DateTimeInput
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.http.request import HttpRequest
from .models import Solicitacao


# class SolicitacaoForm(forms.Form):
#     inicio = DateTimeField(
#         input_formats=['%d/%m/%Y %H:%M'],
#         widget=DateTimeInput(attrs={
#             'class': 'form-control datetimepicker-input',
#             'data-target': '#datetimepicker1'
#         })
#     )

class SolicitacaoForm(ModelForm):

    def __init__(self, agenda, solicitante, *args, **kwargs):
        self.agenda = agenda
        self.solicitante = solicitante
        super().__init__(*args, **kwargs)

    class Meta:
        model = Solicitacao
        fields = ['inicio', 'observacao']
        widgets = {
            'inicio': DateTimeInput(),
        }