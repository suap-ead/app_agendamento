from datetime import date
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django.contrib.admin import register, ModelAdmin, TabularInline, StackedInline
from django.contrib.auth import get_user_model
from tabbed_admin import TabbedModelAdmin
from import_export.admin import ImportExportModelAdmin, ExportActionMixin
from import_export.widgets import Widget, ForeignKeyWidget, ManyToManyWidget
from import_export.resources import ModelResource
from import_export.fields import Field
from .models import Campus, Diretoria, Curso, Turma, TipoVinculo
from .models import Agenda, Vaga, Solicitacao, Autorizacao
from .models import Criterio, AgendaCriterio, CriterioAvaliado


@register(TipoVinculo)
class TipoVinculoAdmin(ImportExportModelAdmin):
    list_display = ["descricao"]
    search_fields = ["descricao"]


class CampusResource(ModelResource):
    class Meta:
        model = Campus
        import_id_fields = ('sigla', )
        fields = ('suap_id', 'sigla', 'descricao', 'url', 'active',)



@register(Campus)
class CampusAdmin(ImportExportModelAdmin):
    list_display = ['sigla', 'descricao', 'active']
    search_fields = ['sigla', 'descricao', 'suap_id', 'url']
    list_filter = ['active']
    resource_class = CampusResource


class DiretoriaResource(ModelResource):
    campus = Field(column_name='campus',
        attribute='campus', widget=ForeignKeyWidget(Campus, 'sigla'))
        
    class Meta:
        model = Diretoria
        import_id_fields = ('campus', 'sigla',)
        fields = ('campus', 'sigla', 'descricao', 'active',)


@register(Diretoria)
class DiretoriaAdmin(ImportExportModelAdmin):
    list_display = ['sigla', 'campus', 'descricao', 'active']
    search_fields = ['sigla', 'descricao']
    list_filter = ['active', 'campus']
    resource_class = DiretoriaResource


class DiretoriaWidget(Widget):
    def clean(self, value, row=None, *args, **kwargs):
        if value:
            parts = value.split('/')
            return Diretoria.objects.get(
                sigla__iexact=parts[0],
                campus__sigla__iexact=parts[1]
            )
        else:
            return None

    def render(self, value, obj=None):
        if value is None:
            return ""
        return f"{value.sigla}/{value.campus.sigla}"


class CursoResource(ModelResource):
    diretoria = Field(column_name='diretoria',
        attribute='diretoria', widget=DiretoriaWidget())

    class Meta:
        model = Curso
        import_id_fields = ('codigo', )
        fields = ('diretoria', 'codigo', 'nome', 'descricao', 'active',)


@register(Curso)
class CursoAdmin(ImportExportModelAdmin):
    list_display = ['nome', 'codigo', 'active']
    search_fields = ['codigo', 'nome', 'descricao']
    list_filter = ['active', 'diretoria']
    resource_class = CursoResource


class CursoWidget(Widget):
    def clean(self, value, row=None, *args, **kwargs):
        if value:
            parts = value.split(' - ')
            return Curso.objects.get(codigo=parts[0])
        else:
            return None


class TurmaResource(ModelResource):
    curso = Field(column_name='curso', attribute='curso', widget=CursoWidget())

    class Meta:
        model = Turma
        import_id_fields = ('codigo', )
        fields = ('codigo', 'curso', 'active',)


@register(Turma)
class TurmaAdmin(ImportExportModelAdmin):
    list_display = ['codigo', 'curso', 'active']
    search_fields = ['codigo']
    list_filter = ['active', 'curso']
    autocomplete_fields = ['curso']
    resource_class = TurmaResource


@register(Criterio)
class CriterioAdmin(ImportExportModelAdmin):
    list_display = ['titulo']
    search_fields = ['titulo']


class AgendaCriterioInline(TabularInline):
    model = AgendaCriterio
    extra = 0
    autocomplete_fields = ('criterio',)


class VagaInline(TabularInline):
    model = Vaga
    extra = 0


class AutorizacaoInline(TabularInline):
    model = Autorizacao
    extra = 0
    autocomplete_fields = ('user',)


class VagaWidget(Widget):
    def clean(self, value, row=None, *args, **kwargs):
        if value:
            parts = value.split('/')
            return Diretoria.objects.get(
                sigla__iexact=parts[0],
                campus__sigla__iexact=parts[1]
            )
        else:
            return None

    def render(self, value, obj=None):
        result = ""
        print(value, obj)
        if value is None:
            return result

        for x in obj.vagas:
            result += f"({x.dia}/{x.inicio}/{x.fim}/{x.atendimentos})"
        return result



@register(Agenda)
class AgendaAdmin(TabbedModelAdmin, ImportExportModelAdmin):
    list_display = ['nome', 'quando', 'restricoes']
    search_fields = ['nome']
    date_hierarchy = 'inicio'
    autocomplete_fields = ['restrito_aos_campi', 'restrito_aas_diretorias', 'restrito_aos_cursos', 'restrito_aas_turmas', 'restrito_aos_vinculos']

    tab_overview = (
        (None, {'fields': ('nome', 'informacao')}),
    )

    tab_scheduling = (
        (None, {'fields': ('inicio', 'fim', 'janela')}),
        VagaInline
    )

    tab_constraint = (
        (None, {'fields': ('restrito_aos_campi', 'restrito_aas_diretorias', 'restrito_aos_cursos', 'restrito_aas_turmas', 'restrito_aos_vinculos')}),
        AutorizacaoInline
    )

    tab_criteria = (
        AgendaCriterioInline,
    )


    tabs = [
        ( _('Identificação'), tab_overview ),
        ( _('Agendamento'), tab_scheduling ),
        ( _('Restrições'), tab_constraint ),
        ( _('Critérios'), tab_criteria ),
    ]

    def quando(self, instance):
        return mark_safe(
            f"{instance.condicao}<br> De {instance.inicio}<br>Até {instance.fim}<br>A cada {instance.janela} minutos"
        )
    quando.short_description = _("Quando")
    quando.admin_order_field = 'inicio'

    def restricoes(self, instance):
        s = ""
        if instance.restrito_aos_campi.exists():
            s += "Restrito aos campi: %s <br>" % ", ".join(["%s" % x for x in instance.restrito_aos_campi.all()])
        if instance.restrito_aas_diretorias.exists():
            s += "Restrito às diretorias: %s <br>" % ", ".join(["%s" % x for x in instance.restrito_aas_diretorias.all()])
        if instance.restrito_aos_cursos.exists():
            s += "Restrito aos cursos: %s <br>" % ", ".join(["%s" % x.codigo for x in instance.restrito_aos_cursos.all()])
        if instance.restrito_aas_turmas.exists():
            s += "Restrito às turmas: %s <br>" % ", ".join(["%s" % x for x in instance.restrito_aas_turmas.all()])
        if instance.restrito_aas_turmas.exists():
            s += "Restrito aos vínculos: %s <br>" % ", ".join(["%s" % x for x in instance.restrito_aos_vinculos.all()])
        if s == "":
            s = "Não existem restrinções"
        return mark_safe(s)
    restricoes.short_description = _("Restrições")


class Student(object):
    def __init__(self, matricula):
        self.matricula = matricula
        self.ingresso = matricula[0:5]
        self.ano_ingresso = matricula[0:4]
        self.periodo_ingresso = matricula[4:5]
        self.codigo_curso = matricula[5:-4]
        self.curso = Curso.objects.filter(codigo=self.codigo_curso).first()


@register(Solicitacao)
class SolicitacaoAdmin(ImportExportModelAdmin):
    list_display = ['inicio', 'status', 'agenda', 'solicitante', 'avaliador']
    list_filter = [
        'status', 'solicitante__tipo', 'solicitante__categoria', 'agenda__nome', 'solicitante__codigo_curso'
    ]
    search_fields = ['solicitante', 'avaliador', 'status', 'justificativa']
    date_hierarchy = 'inicio'
    autocomplete_fields = ['agenda', 'solicitante']

    def get_exclude(self, request, obj=None):
        if obj is None:
            return ['status', 'avaliador', 'justificativa', 'avaliado_em']

        return ['solicitante', 'inicio', 'fim', 'agenda', 'avaliador', 'avaliado_em']

    # def get_readonly_fields(self, request, obj=None):
    #     if obj:
    #         return []
    #     return []

    def get_form(self, request, obj, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj and 'justificativa' in form.base_fields:
            # form.base_fields['justificativa'].queryset = get_user_model().objects.filter(pk=request.user.pk)
            form.base_fields['justificativa'].required=True
        return form

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        context["is_student"] = obj and len(obj.solicitante.username) > 11
        if obj:
            context["criterios"] = AgendaCriterio.objects.filter(agenda=obj.agenda)
            if context["is_student"]:
                context["student"] = Student(obj.solicitante.username)

        return super().render_change_form(request, context, add, change, form_url, obj)
    def save_model(self, request, obj, form, change):
        if obj.status in [Solicitacao.Status.INDEFERIDO, Solicitacao.Status.DEFERIDO]:
            obj.avaliador = request.user
        obj.save()
        criterios = [int(x) for x in request.POST.getlist('criterio')]
        for criterio in AgendaCriterio.objects.filter(agenda=obj.agenda):
            CriterioAvaliado.objects.update_or_create(
                solicitacao=obj, 
                criterio=criterio,
                defaults={'confere': criterio.id in criterios}
            )
