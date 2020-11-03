from datetime import date
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django.contrib.admin import register, ModelAdmin, TabularInline, StackedInline
from import_export.admin import ImportExportModelAdmin
from .models import Agenda, Vaga, Solicitacao
from .models import Campus, Diretoria, Curso, Turma


@register(Campus)
class CampusAdmin(ModelAdmin):
    list_display = ['sigla', 'descricao', 'active']
    search_fields = ['sigla', 'descricao', 'suap_id', 'url']
    list_filter = ['active']


@register(Diretoria)
class DiretoriaAdmin(ModelAdmin):
    list_display = ['sigla', 'campus', 'descricao', 'active']
    search_fields = ['sigla', 'descricao']
    list_filter = ['active', 'campus']


@register(Curso)
class CursoAdmin(ModelAdmin):
    list_display = ['nome', 'codigo', 'active']
    search_fields = ['codigo', 'nome', 'descricao']
    list_filter = ['active', 'diretoria']


@register(Turma)
class TurmaAdmin(ModelAdmin):
    list_display = ['codigo', 'curso', 'active']
    search_fields = ['codigo']
    list_filter = ['active', 'curso']


class VagaInline(TabularInline):
    model = Vaga
    extra = 0


@register(Agenda)
class AgendaAdmin(ImportExportModelAdmin):
    list_display = ['nome', 'quando', 'restricoes', 'is_active']
    search_fields = ['nome']
    date_hierarchy = 'inicio'
    inlines = [VagaInline]
    autocomplete_fields = ['restrito_aos_campi', 'restrito_aas_diretorias', 'restrito_aos_cursos', 'restrito_aas_turmas']

    def is_active(self, instance):
        hoje = date.today()
        if hoje >= instance.inicio and hoje <= instance.fim:
            return "Ativo"
        return "Inativo"
    is_active.short_description = _("Ativo?")

    def quando(self, instance):
        return mark_safe(f"De {instance.inicio}<br>Até {instance.fim}<br>A cada {instance.janela} minutos")
    quando.short_description = _("Quando")
    quando.admin_order_field = 'inicio'

    def restricoes(self, instance):
        s = ""
        if instance.restrito_aos_campi.exists():
            s += "Restrito aos campi: %s <br>" % ["%s" % x for x in instance.restrito_aos_campi.all()]
        if instance.restrito_aas_diretorias.exists():
            s += "Restrito às diretorias: %s <br>" % ["%s" % x for x in instance.restrito_aas_diretorias.all()]
        if instance.restrito_aos_cursos.exists():
            s += "Restrito aos cursos: %s <br>" % ["%s" % x for x in instance.restrito_aos_cursos.all()]
        if instance.restrito_aas_turmas.exists():
            s += "Restrito às turmas: %s <br>" % ["%s" % x for x in instance.restrito_aas_turmas.all()]
        if s == "":
            s = "Não existem restrinções"
        return mark_safe(s)
    restricoes.short_description = _("Restrições")


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
