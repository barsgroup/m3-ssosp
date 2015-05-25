# coding: utf-8
u"""
Настройки
"""
from django.conf import settings

# Пример настроек в settings.py
# SSO_CONFIG = {
#     'idp': 'https://localhost:9443/samlsso',
#     'issuer': 'saml2.demo',
#     'index': '1537824998',
#     'acs': '/sso/acs/',
#     'session_map': 'ssosp.backends.db',
#     'cache_timeout': 2592000,
# }


# Словарь конфигурации модуля по-умолчанию
DEFAULT_SSO_CONFIG = {
    'idp': '',
    'issuer': '',
    'index': '',
    'acs': '',
    'session_map': 'ssosp.backends.db',
    'signing': False,
    'validate': False,
    'zipped': False,
    'cache_timeout': 2592000,  # 30 days by default
}


def get_sso_setting(key):
    u"""
    Получение значения настройки

    :param basestring key: настройка
    :return: значение настройки
    """
    return settings.SSO_CONFIG.get(key) or DEFAULT_SSO_CONFIG.get(key) or None