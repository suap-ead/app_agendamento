# Generated by Django 3.1.2 on 2020-11-03 20:55

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('agendamento', '0002_autorizacao'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='autorizacao',
            unique_together={('agenda', 'user')},
        ),
    ]
