#coding:utf-8
u"""
Модель хранения соответствия SSO-сессии и django-сессии
"""

from __future__ import absolute_import
from django.db import models
from django.utils.translation import ugettext_lazy as _


class SSOSession(models.Model):
    u"""
    Модель хранения соответствия ключа SSO-сессии и django-сессии
    """
    sso_session_key = models.CharField(_('sso_session key'), max_length=40, primary_key=True)
    django_session_key = models.CharField(_('django_session key'), max_length=40)

    class Meta:
        db_table = 'sso_session'
        verbose_name = _('sso session')
        verbose_name_plural = _('sso sessions')