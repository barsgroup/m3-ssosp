#coding:utf-8
u"""
Базовый класс для бэкенда соответствия
"""


class BaseSSOSessionMap(object):
    u"""
    Интерфейс бэкенда соответствия сессий
    """
    def get_django_session_key(self, sso_session_key):
        u"""
        Получить идентификатор django-сессии по идентификатору SSO-сессии

        :param basestring sso_session_key: идентификатор SSO-сессии
        :return: идентификатор django-сессии
        :rtype: basestring
        """
        raise NotImplementedError

    def get_sso_session_key(self, django_session_key):
        u"""
        Получить идентификатор SSO-сессии по идентификатору django-сессии

        :param basestring sso_session_key: идентификатор django-сессии
        :return: идентификатор SSO-сессии
        :rtype: basestring
        """
        raise NotImplementedError

    def exists_sso_session(self, sso_session_key):
        u"""
        Проверить существование идентификатора SSO-сессии

        :param basestring sso_session_key: идентификатор SSO-сессии
        :return: признак существования идентификатора
        :rtype: bool
        """
        raise NotImplementedError

    def exists_django_session(self, django_session_key):
        u"""
        Проверить существование идентификатора django-сессии

        :param basestring django_session_key: идентификатор django-сессии
        :return: признак существования идентификатора
        :rtype: bool
        """
        raise NotImplementedError

    def set_session_map(self, sso_session_key, django_session_key):
        u"""
        Установить соответствие идентификатора SSO-сессии и django-сессии

        :param basestring sso_session_key: идентификатор SSO-сессии
        :param basestring django_session_key: идентификатор django-сессии
        """
        raise NotImplementedError

    def delete_by_sso_session(self, sso_session_key):
        u"""
        Удалить соответствие по идентификатору SSO-сессии

        :param basestring sso_session_key: идентификатор SSO-сессии
        """
        raise NotImplementedError

    def delete_by_django_session(self, django_session_key):
        u"""
        Удалить соответствие по идентификатору django-сессии

        :param basestring django_session_key: идентификатор django-сессии
        """
        raise NotImplementedError