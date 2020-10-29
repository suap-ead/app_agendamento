from datetime import date
from django.utils.translation import gettext as _
from django.contrib.admin import register, ModelAdmin, TabularInline, StackedInline
from import_export.admin import ImportExportModelAdmin
from .models import Agenda, Vaga, Solicitacao


class VagaInline(TabularInline):
    model = Vaga
    extra = 0


@register(Agenda)
class AgendaAdmin(ImportExportModelAdmin):
    list_display = ['nome', 'janela', 'inicio', 'fim', 'is_active']
    search_fields = ['nome']
    date_hierarchy = 'inicio'
    inlines = [VagaInline]

    def is_active(self, instance):
        hoje = date.today()
        if hoje >= instance.inicio and hoje <= instance.fim:
            return "Ativo"
        return "Inativo"
    is_active.short_description = _("Ativo?")


@register(Solicitacao)
class SolicitacaoAdmin(ImportExportModelAdmin):
    list_display = ['solicitante', 'inicio', 'fim', 'agenda', 'avaliador', 'status']
    list_filter = ['status', 'agenda__nome']
    search_fields = ['solicitante', 'avaliador', 'status', 'justificativa']
    date_hierarchy = 'inicio'

    def get_readonly_fields(self, request, obj=None):
        if obj: # editing an existing object
            return ['solicitante', 'inicio', 'fim', 'agenda']
        return []
