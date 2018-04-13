#coding:utf-8
u"""
Бэкенд хранения соответствия сессий в базе данных
"""
from __future__ import absolute_import
from django.db import router, transaction, IntegrityError
from ssosp.backends.base import BaseSSOSessionMap
from ssosp.models import SSOSession


class SSOSessionMap(BaseSSOSessionMap):
    u"""
    Бэкенд хранения соответствия сессий в базе данных
    """
    def get_django_session_key(self, sso_session_key):
        try:
            s = SSOSession.objects.get(sso_session_key=sso_session_key)
            return s.django_session_key
        except SSOSession.DoesNotExist:
            return None

    def get_sso_session_key(self, django_session_key):
        try:
            s = SSOSession.objects.get(django_session_key=django_session_key)
            return s.sso_session_key
        except SSOSession.DoesNotExist:
            return None

    def exists_sso_session(self, sso_session_key):
        return SSOSession.objects.filter(sso_session_key=sso_session_key).exists()

    def exists_django_session(self, django_session_key):
        return SSOSession.objects.filter(django_session_key=django_session_key).exists()

    def set_session_map(self, sso_session_key, django_session_key):
        if self.exists_sso_session(sso_session_key):
            self.delete_by_sso_session(sso_session_key)
        obj = SSOSession(
            sso_session_key=sso_session_key,
            django_session_key=django_session_key,
        )
        using = router.db_for_write(SSOSession, instance=obj)
        sid = transaction.savepoint(using=using)
        try:
            obj.save(using=using, force_insert=True)
        except IntegrityError:
            transaction.savepoint_rollback(sid, using=using)
            raise

    def delete_by_sso_session(self, sso_session_key):
        try:
            SSOSession.objects.get(sso_session_key=sso_session_key).delete()
        except SSOSession.DoesNotExist:
            pass

    def delete_by_django_session(self, django_session_key):
        try:
            SSOSession.objects.get(django_session_key=django_session_key).delete()
        except SSOSession.DoesNotExist:
            pass