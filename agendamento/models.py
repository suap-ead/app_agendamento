import calendar
from datetime import datetime, date, time, timedelta
from django.core.mail import send_mail
from django.utils.translation import gettext as _
from django.utils.timezone import now, localtime, make_aware
from django.db.models import Model, TextChoices
from django.db.models import DateField, BooleanField, NullBooleanField, DateTimeField, TextField, TimeField, PositiveIntegerField
from django.db.models import ImageField
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db.models import Model, CharField, EmailField, BooleanField, DateTimeField, ForeignKey, CASCADE
from django.db.models import ForeignKey, CASCADE
from suap_ead.fields import StringField, NullStringField, nullable, nullable_phone, FK, NullFK
from django.contrib.auth import get_user_model
from threading import current_thread
from sc4py.datetime import today, daterange
from datetimerange import DateTimeRange
from django.forms.models import model_to_dict


class Agenda(Model):
    nome = StringField(_('Nome da agenda'))
    janela = PositiveIntegerField(_("Janela de atendimento (min)"), help_text=_("Alterar a janela depois de já ter solicitações não muda a tempo da reserva da solicitação"))
    inicio = DateField(_('Início'), help_text=_("Esta agenda começa que dia? Alterar a data de início da agenda não altera as solicitações"))
    fim = DateField(_('Fim'), help_text=_("Esta agenda termina que dia. Alterar a data de fim da agenda não altera as solicitações"))
    informacao = TextField(_('Informações aos solicitantes'), **nullable)

    class Meta:
        verbose_name = _("Agenda")
        verbose_name_plural = _("Agendas")
        ordering = ['inicio']

    def __str__(self):
        return f"{self.nome}"

    @classmethod
    def agendas_abertas(cls):
        return Agenda.objects.filter(fim__gte=date.today())

    def solicitacoes_futuras(self, user=None):
        return Solicitacao.objects.filter(inicio__gte=now())

    @property
    def vagas_futuras(self):
        result = []

        vagas = {}
        for x in self.vaga_set.all():
            if int(x.dia) not in vagas:
                vagas[int(x.dia)] = []
            vagas[int(x.dia)].append(x)

        dias = set([int(x.dia) for x in self.vaga_set.all()])

        for data in daterange(max(self.inicio, today()), self.fim):
            if data.weekday() in dias:
                for vaga in vagas[d.weekday()]:
                    result.append({ "dia": d, "vaga": vaga })
        return result

    def solicitacao_futura(self, solicitante):
        return Solicitacao.objects.filter(
            agenda=self, inicio__gte=now(), status__in=Solicitacao.bloqueantes, solicitante=solicitante
        ).order_by('inicio').first()

    @property
    def datas_futuras(self):
        dias = set([int(x.dia) for x in self.vaga_set.all()])
        return [data for data in daterange(max(self.inicio, today()), self.fim) if data.weekday() in dias]

    def horarios_futuros(self, data, solicitante):
        quando = self.solicitacao_futura(solicitante)
        if quando is not None:
            inicio = localtime(quando.inicio).strftime('%d/%m/%Y às %H:%M')
            raise Exception(f"Você já tem uma solicitação prevista para {inicio} na situação {quando.status}")
            
        if not (max(self.inicio, date.today()) <= data.date() <= self.fim):
            raise Exception(f"A data deve ser entre {self.inicio} e {self.fim}, mas você informou a data {data}.")

        result = []
        for vaga in self.vaga_set.filter(dia=data.weekday()):
            time_range = DateTimeRange(datetime.combine(data, vaga.inicio), datetime.combine(data, vaga.fim))
            for dt in time_range.range(timedelta(minutes=self.janela)):
                if make_aware(dt) > now():
                    quantidade = Solicitacao.objects.filter(
                        agenda=self, 
                        inicio=dt, 
                        status__in=[Solicitacao.Status.DEFERIDO, Solicitacao.Status.SOLICITADO]
                    ).count()
                    if quantidade < vaga.atendimentos:
                        result.append(dt)
        return result[:-1]


class Vaga(Model):
    class DiaDaSemana(TextChoices):
        SEGUNDA = str(calendar.MONDAY), _('Seg')
        TERCA = str(calendar.TUESDAY), _('Ter')
        QUARTA = str(calendar.WEDNESDAY), _('Qua')
        QUINTA = str(calendar.THURSDAY), _('Qui')
        SEXTA = str(calendar.FRIDAY), _('Sex')
        SAB = str(calendar.SATURDAY), _('Sab')
        DOM = str(calendar.SUNDAY), _('Dom')
    agenda = FK(_('Agenda'), Agenda)
    dia = StringField(_('Dia da semana'), choices=DiaDaSemana.choices)
    inicio = TimeField(_('Início'))
    fim = TimeField(_('Fim'))
    atendimentos = PositiveIntegerField(_('Quantidade de atendimentos na janela'))

    class Meta:
        verbose_name = _("Vaga")
        verbose_name_plural = _("Vagas")
        ordering = ['dia', 'inicio']

    def __str__(self):
        return f"Até {self.atendimentos} atendimentos no dia {self.dia}, das {self.inicio} às {self.fim}"



class Solicitacao(Model):
    class Status(TextChoices):
        SOLICITADO = 'Solicitado', _('Solicitado')
        DEFERIDO = 'Deferido', _('Deferido')
        INDEFERIDO = 'Indeferido', _('Indeferido')
        CANCELADO = 'Cancelado', _('Cancelado')

    bloqueantes = [Status.SOLICITADO, Status.DEFERIDO]

    agenda = FK(_('Agenda'), Agenda)
    inicio = DateTimeField(_("Agendado para"))
    fim = DateTimeField(_("Termina em"))
    solicitante = FK(_('Solicitante'), get_user_model(), related_name="solicitantes")
    status = StringField(_('Status'), choices=Status.choices, default=Status.SOLICITADO)
    avaliador = NullFK('Avaliador', get_user_model(), related_name="avaliadores")
    justificativa = TextField(_('Justificativa'), **nullable)


    class Meta:
        verbose_name = _("Solicitação")
        verbose_name_plural = _("Solicitações")
        ordering = ['inicio']

    def __str__(self):
        avaliado_por = f"por {self.avaliador}." if self.status != Solicitacao.Status.SOLICITADO else "."
        return f"De {self.inicio} às {self.fim}, horário reservado para {self.solicitante}. {self.status}" + avaliado_por

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        agora = localtime(now()).strftime('%d/%m/%Y às %H:%M')
        inicio = self.inicio.strftime('%d/%m/%Y às %H:%M')
        if self.solicitante.email is not None and self.solicitante.email != '':
            SUBJECT = 'subject'
            TEMPLATE = 'template'
            messages = {
                Solicitacao.Status.SOLICITADO: {
                    SUBJECT: _("Solicitação de agendamento"),
                    TEMPLATE: _('Você está recebendo esta mensagem pois em {agora} você SOLICITOU um agendamento para {inicio}.'
                                ' Lembre-se de chegar uns 15 minutos antes.'),
                },
                Solicitacao.Status.DEFERIDO: {
                    SUBJECT: _("Agendamento aprovado"),
                    TEMPLATE: _('Você está recebendo esta mensagem pois em {agora} seu agendamento para {inicio} foi APROVADO.'
                                ' Lembre-se de chegar uns 15 minutos antes.'),
                },
                Solicitacao.Status.INDEFERIDO: {
                    SUBJECT: _("Agendamento negado"),
                    TEMPLATE: _('Você está recebendo esta mensagem pois em {agora} seu agendamento para {inicio} foi NEGADO'
                                ' pelo seguinte motivo: {justificativa}.'),
                },
                Solicitacao.Status.CANCELADO: {
                    SUBJECT: _("Agendamento cancelado"),
                    TEMPLATE: _('Você está recebendo esta mensagem pois em {agora} seu agendamento para {inicio} foi CANCELADO.'
                                ' Se não foi feito por você, favor realizar outro agendamento.'),
                },
            }
            send_mail(
                messages[self.status][SUBJECT],
                messages[self.status][TEMPLATE].format(agora=agora, inicio=inicio, justificativa=self.justificativa),
                None,
                [self.solicitante.email],
                fail_silently=True,
            )
