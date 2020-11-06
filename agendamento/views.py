import json
from datetime import datetime, timedelta
from django.conf import settings
from django.utils.translation import gettext as _
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Agenda, Solicitacao
from .forms import SolicitacaoForm


@login_required
def index(request):
    agendas = Agenda.objects.all()
    solicitacoes = Solicitacao.objects.filter(solicitante=request.user)
    return render(
        request, 
        'agendamento/index.html', 
        context={
            'agendas': agendas,
            'solicitacoes': solicitacoes,
            'title': _('Início'),
            'site_url': settings.ADMIN_SITE_URL,
            'site_header': settings.ADMIN_SITE_HEADER,
            'index_title': settings.ADMIN_SITE_TITLE,
        }
    )


@login_required
def agenda_selecionar(request):
    agendas = Agenda.agendas_abertas()
    return render(
        request, 
        'agendamento/agenda_selecionar.html', 
        context={
            'agendas': agendas,
            'title': _('Selecione uma agenda'),
            'site_url': settings.ADMIN_SITE_URL,
            'site_header': settings.ADMIN_SITE_HEADER,
            'index_title': settings.ADMIN_SITE_TITLE,
        }
    )


@login_required
def solicitacao_cancelar(request, id):
    solicitacao = get_object_or_404(Solicitacao, id=id, solicitante=request.user)
    solicitacao.status = solicitacao.Status.CANCELADO
    solicitacao.save(update_fields={"status"})
    return redirect("agendamento:index")

@login_required
def agenda_ver(request, id):
    agenda = get_object_or_404(Agenda, id=id)

    if request.method == 'POST':
        form = SolicitacaoForm(agenda, request.user, request.POST)
        inicio = datetime.fromisoformat(form.data['inicio'])
        Solicitacao.objects.create(agenda=agenda, solicitante=request.user, inicio=inicio, fim=inicio + timedelta(minutes=agenda.janela))
        return redirect("agendamento:index")
    else:
        form = SolicitacaoForm(agenda, request.user)
    return render(
        request, 
        'agendamento/agenda_ver.html', 
        context={
            'agenda': agenda,
            'form': form,
            'title': _('Escolha um dia/horário para agendar'),
            'site_url': settings.ADMIN_SITE_URL,
            'site_header': settings.ADMIN_SITE_HEADER,
            'index_title': settings.ADMIN_SITE_TITLE,
        }
    )


@login_required
def agenda_horarios_futuros(request, id, data):
    try:
        agenda = get_object_or_404(Agenda, id=id)
        return JsonResponse(agenda.horarios_futuros(datetime.strptime(data, '%Y-%m-%d'), request.user), safe=False)
    except Exception as err:
        return JsonResponse({"error_message": str(err)}, status=412)
