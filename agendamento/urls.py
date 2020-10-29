from django.urls import path
from .views import index, agenda_selecionar, agenda_ver, agenda_horarios_futuros, solicitacao_cancelar


app_name = 'agendamento'

urlpatterns = [
    path('', index, name='index'),
    path('agendas/', agenda_selecionar, name='agenda_selecionar'),
    path('agendas/<int:id>/', agenda_ver, name='agenda_ver'),
    path('agendas/<int:id>/<data>/', agenda_horarios_futuros, name='agenda_horarios_futuros'),
    path('solicitacao/<int:id>/cancelar', solicitacao_cancelar, name='solicitacao_cancelar'),
]
