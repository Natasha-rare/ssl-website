# Generated by Django 4.2 on 2023-05-11 14:46

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('classes', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='gameregister',
            name='attendance',
            field=models.CharField(choices=[('Сыграл', 'Played'), ('Не пришел', 'Skip'), ('Опоздал', 'Late')], default='Сыграл', max_length=30, verbose_name='Посещаемость'),
        ),
        migrations.AlterField(
            model_name='game',
            name='date',
            field=models.DateField(default=datetime.date(2023, 5, 13)),
        ),
        migrations.AlterField(
            model_name='gameregister',
            name='date',
            field=models.DateField(default=datetime.date(2023, 5, 13)),
        ),
    ]
