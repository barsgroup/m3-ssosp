# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-07-18 17:24
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SSOSession',
            fields=[
                ('sso_session_key', models.CharField(max_length=40, primary_key=True, serialize=False, verbose_name='sso_session key')),
                ('django_session_key', models.CharField(max_length=40, verbose_name='django_session key')),
            ],
            options={
                'db_table': 'sso_session',
                'verbose_name': 'sso session',
                'verbose_name_plural': 'sso sessions',
            },
        ),
    ]
