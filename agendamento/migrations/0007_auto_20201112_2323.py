# Generated by Django 3.1.2 on 2020-11-12 23:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agendamento', '0006_agenda_restrito_aos_vinculos'),
    ]

    operations = [
        migrations.AddField(
            model_name='solicitacao',
            name='cancelado_em',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Cancelado'),
        ),
        migrations.AddField(
            model_name='solicitacao',
            name='observacao',
            field=models.TextField(blank=True, null=True, verbose_name='Observação'),
        ),
    ]
