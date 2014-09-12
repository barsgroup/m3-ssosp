#coding:utf-8
u"""
Классы SAML-запросов и ответов
"""
import urllib2
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import logout, login
from django.shortcuts import redirect
from django.utils.importlib import import_module
from ssosp.assertion_parser import xml_to_assertion, is_logout_request, \
    get_session_from_request_assertion, build_assertion, assertion_to_xml, \
    is_logout_response, get_session_from_response_assertion, \
    get_userid_from_assertion, get_attributes_from_assertion, \
    verify_assertion, sign_request
from ssosp.exceptions import SSOLoginException
from ssosp.utils import decode_base64_and_inflate, deflate_and_base64_encode, \
    get_random_id, get_time_string, decode_base64


# Пример настроек в settings.py
# SSO_CONFIG = {
#     'idp': 'https://localhost:9443/samlsso',
#     'issuer': 'saml2.demo',
#     'index': '1537824998',
#     'acs': '/sso/acs/',
#     'session_map': 'ssosp.backends.db'
# }


# Словарь конфигурации модуля по-умолчанию
DEFAULT_SSO_CONFIG = {
    'session_map': 'ssosp.backends.db',
    'signing': False,
    'validate': False,
    'zipped': False,
}


class SSOException(Exception):
    u"""
    Класс исключений работы с SSO
    """
    pass


def get_session_map():
    u"""
    Получение бэкенда хранения соответствия сессий, указанного в
    настройке SSO_CONFIG['session_map']

    :return: Экземпляр бэкенда, наследника BaseSSOSessionMap
    :rtype: ssosp.backends.base.BaseSSOSessionMap
    """
    config = settings.SSO_CONFIG or DEFAULT_SSO_CONFIG
    session_map_engine = config.get('session_map', None)
    engine = import_module(session_map_engine)
    return engine.SSOSessionMap()


def get_method(method_str):
    u"""
    Получение функции, представленной строкой с полным путем

    :param basesting method_str: полный путь к функции
    :return: указатель на функцию или None, если строка пустая
    """
    if method_str:
        module = '.'.join(method_str.split('.')[:-1])
        method = method_str.split('.')[-1]
        mod = import_module(module)
        return getattr(mod, method)
    else:
        return None


class SAMLObject(object):
    u"""
    Базовый класс SAML-объекта
    """
    def __init__(self, request):
        u"""
        Инициализация

        :param request: запрос, в рамках которого создан объект
        :type request: django.http.HttpRequest
        """
        self.config = settings.SSO_CONFIG or DEFAULT_SSO_CONFIG
        self.idp_url = self.config.get('idp', '')
        self.issuer = self.config.get('issuer', '')
        self.service_index = self.config.get('index', '')
        self.acs_url = request.build_absolute_uri(self.config.get('acs', ''))
        self.signing = self.config.get('signing', False)
        self.validate = self.config.get('validate', False)
        self.public_key_str = self.config.get('public_key', None)
        self.private_key_str = self.config.get('private_key', None)
        self.logout_method = get_method(self.config.get('logout', None))
        self.login_method = get_method(self.config.get('login', None))
        self.get_user_method = get_method(self.config.get('get_user', None))


class AuthResponse(SAMLObject):
    u"""
    SAML-ответ на запрос аутентификации
    """
    def __init__(self, request):
        super(AuthResponse, self).__init__(request)

    def from_assertion(self, assertion):
        u"""
        Заполнить из утверждения. Загрузить.
        Определяется сессия, пользователь, атрибуты пользователя.

        :param assertion: Утверждение, из которого надо получить данные
        :type assertion: etree.ElementTree
        """
        if self.validate and (not self.public_key_str
                              or not verify_assertion(assertion,
                                                      self.public_key_str)):
            raise SSOException("Response not valid")
        self.session_id = get_session_from_response_assertion(assertion)
        self.attributes = get_attributes_from_assertion(assertion)
        userid = get_userid_from_assertion(assertion)
        if self.get_user_method:
            self.user = self.get_user_method(userid, self.attributes)
        else:
            try:
                self.user = User.objects.get(username=userid)
                # возьмем первый попавшийся бэкенд
                self.user.backend = settings.AUTHENTICATION_BACKENDS[0]
            except User.DoesNotExist:
                self.user = None

    def do_login(self, request, next_url):
        u"""
        Выполнить вход в систему.
        Атрибуты пользователя сохраняются в сессию.
        Сохраняется соответствие SSO-сессии и django-сессии.

        :param request: запрос, в рамках которого выполняется действие
        :type request: django.http.HttpRequest
        :param basestring next_url: адрес, на который вернуться после входа
        :return: ответ на запрос - редирект на адрес возврата
        :rtype: django.http.HttpResponseRedirect
        """
        if self.login_method:
            try:
                self.login_method(request, self.user)
            except SSOLoginException as ex:
                return redirect(u'{}?msg={}'.format(ex.next_url, ex.message))
        else:
            login(request, self.user)

        request.session['attributes'] = self.attributes
        # сохраним соответствие SSO-сессии и django-сессии
        if self.session_id:
            session_map = get_session_map()
            session_map.set_session_map(self.session_id,
                                        request.session.session_key)
        return redirect(next_url)


class LogoutResponse(SAMLObject):
    u"""
    SAML-ответ на запрос выхода из системы
    """
    def __init__(self, request):
        super(LogoutResponse, self).__init__(request)

    def from_assertion(self, assertion):
        u"""
        Заполнить из утверждения. Загрузить.
        Просто проверим цифровую подпись, если надо.

        :param assertion: Утверждение, из которого надо получить данные
        :type assertion: etree.ElementTree
        """
        if self.validate and (not self.public_key_str
                              or not verify_assertion(assertion,
                                                      self.public_key_str)):
            raise SSOException("Response not valid")

    def do_logout(self, request, next_url):
        u"""
        Выполнить выход из системы.
        Удаляется соответствие SSO-сессии и django-сессии.

        :param request: запрос, в рамках которого выполняется действие
        :type request: django.http.HttpRequest
        :param basestring next_url: адрес, на который вернуться после выхода
        :return: ответ на запрос - редирект на адрес возврата
        :rtype: django.http.HttpResponseRedirect
        """
        session_map = get_session_map()
        session_key = request.session.session_key
        if self.logout_method:
            self.logout_method(request)
        else:
            logout(request)
        session_map.delete_by_django_session(session_key)
        return redirect(next_url)


class AuthRequest(SAMLObject):
    u"""
    SAML-запрос на вход в систему
    """
    def __init__(self, request):
        super(AuthRequest, self).__init__(request)

    def get_request(self):
        u"""
        Получить SAML-запрос.
        Формируется утверждение AuthnRequest и преобразовывается в строку.

        :return: Утверждение для входа в систему, представленное в виде строки
        :rtype: basestring
        """
        assertion_struct = {
            'tag': '{samlp}AuthnRequest',
            'attrs': {
                'AssertionConsumerServiceURL': self.acs_url,
                'Destination': self.idp_url,
                'ID': get_random_id(),
                'IssueInstant': get_time_string(),
                'ProtocolBinding':
                    "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                'Version': "2.0",
            },
            'nsmap': {'samlp': 'urn:oasis:names:tc:SAML:2.0:protocol',
                      'saml': 'urn:oasis:names:tc:SAML:2.0:assertion'},
            'value': [
                {
                    'tag': '{saml}Issuer',
                    'value': self.issuer,
                },
                {
                    'tag': '{saml}AttributeQuery',
                    'value': [
                        {
                            'tag': '{saml}Attribute',
                            'attrs': {'Name': 'role'}
                        }
                    ]
                }
            ],
        }
        if self.service_index:
            assertion_struct['attrs']['AttributeConsumingServiceIndex'] = \
                self.service_index
        assertion = build_assertion(assertion_struct)
        req = get_str_from_assertion(assertion)
        return req

    def get_login(self, next_url):
        u"""
        Получить GET-запрос на вход в систему.

        :param basestring next_url: адрес, на который вернуться после входа
        :return: редирект на адрес SSO с SAML-запросом на вход в качестве
            параметра
        :rtype: django.http.HttpResponseRedirect
        """
        request_str = self.get_request()
        if self.signing and self.private_key_str:
            req = 'SAMLRequest=%s&RelayState=%s&SigAlg=%s' % (
                urllib2.quote(request_str),
                urllib2.quote(next_url),
                urllib2.quote('http://www.w3.org/2000/09/xmldsig#rsa-sha1'),
            )
            signature = sign_request(req, self.private_key_str)
            login_url = '%s?%s&Signature=%s' % (
                self.idp_url, req,
                urllib2.quote(signature),
            )
        else:
            login_url = '%s?SAMLRequest=%s&RelayState=%s' % (
                self.idp_url, urllib2.quote(request_str), urllib2.quote(next_url)
            )
        return redirect(login_url)


class LogoutRequest(SAMLObject):
    u"""
    SAML-запрос на выход из системы
    """
    def __init__(self, request):
        super(LogoutRequest, self).__init__(request)
        session_map = get_session_map()
        self.session_id = session_map.get_sso_session_key(
            request.session.session_key)

    def from_assertion(self, assertion):
        u"""
        Заполнить из утверждения. Загрузить.
        Просто проверим цифровую подпись, если надо.
        И вытащим сессию, если ее передали в утверждении.

        :param assertion: Утверждение, из которого надо получить данные
        :type assertion: etree.ElementTree
        """
        if self.validate and (not self.public_key_str
                              or not verify_assertion(assertion,
                                                      self.public_key_str)):
            raise SSOException("Response not valid")
        self.session_id = get_session_from_request_assertion(assertion)

    def do_logout_by_session(self, request):
        u"""
        Осуществить выход из систему по сессии SSO.

        :param request: запрос, в рамках которого выполняется действие
        :type request: django.http.HttpRequest
        """
        session_map = get_session_map()
        # найдем django-сессию, соответствующую SSO-сессии
        if session_map.exists_sso_session(self.session_id):
            engine = import_module(settings.SESSION_ENGINE)
            session_key = session_map.get_django_session_key(self.session_id)
            request.session = engine.SessionStore(session_key)
            if self.logout_method:
                self.logout_method(request)
            else:
                logout(request)
            session_map.delete_by_sso_session(self.session_id)
        else:
            # на нашли соответствующую сессию
            pass

    def get_request(self, username):
        u"""
        Получить SAML-запрос на выход.
        Формируется утверждение LogoutRequest и преобразовывается в строку.
        Используется текущая сессия: либо загруженная, либо определенная из
        request.

        :param basestring username: пользователь, который должен выйти из
            системы. (Похоже, что уже не надо использовать)
        :return: Утверждение для выхода из системы, представленное в виде строки
        :rtype: basestring
        """
        assertion_struct = {
            'tag': '{samlp}LogoutRequest',
            'attrs': {
                'AssertionConsumerServiceURL': self.acs_url,
                'ID': get_random_id(),
                'Destination': self.idp_url,
                'IssueInstant': get_time_string(),
                'ProtocolBinding': "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                'Version': "2.0",
                'AttributeConsumingServiceIndex': self.service_index,
            },
            'nsmap': {'samlp': 'urn:oasis:names:tc:SAML:2.0:protocol',
                      'saml': 'urn:oasis:names:tc:SAML:2.0:assertion'},
            'value': [
                {
                    'tag': '{saml}Issuer',
                    'value': self.issuer,
                },
                {
                    'tag': '{saml}NameID',
                    'value': username,
                },
            ],
        }
        if self.session_id:
            assertion_struct['value'].append({
                'tag': '{samlp}SessionIndex',
                'value': self.session_id,
            })
        assertion = build_assertion(assertion_struct)
        req = get_str_from_assertion(assertion)
        return req

    def get_logout(self, username, next_url):
        u"""
        Получить GET-запрос на выход из системы.

        :param basestring username: пользователь, который должен выйти из
            системы. (Похоже, что уже не надо использовать)
        :param basestring next_url: адрес, на который вернуться после входа
        :return: редирект на адрес SSO с SAML-запросом на выход в качестве
            параметра
        :rtype: django.http.HttpResponseRedirect
        """
        request_str = self.get_request(username)
        if self.signing and self.private_key_str:
            req = 'SAMLRequest=%s&RelayState=%s&SigAlg=%s' % (
                urllib2.quote(request_str),
                urllib2.quote(next_url),
                urllib2.quote('http://www.w3.org/2000/09/xmldsig#rsa-sha1'),
            )
            signature = sign_request(req, self.private_key_str)
            logout_url = '%s?%s&Signature=%s' % (
                self.idp_url, req,
                urllib2.quote(signature),
            )
        else:
            logout_url = '%s?SAMLRequest=%s&RelayState=%s' % (
                self.idp_url, urllib2.quote(request_str),
                urllib2.quote(next_url)
            )
        return redirect(logout_url)

    def do_logout(self, request):
        u"""
        Осуществить выход из систему по текущей сессии django.
        Сессия получается из текущего запроса.

        :param request: запрос, в рамках которого выполняется действие
        :type request: django.http.HttpRequest
        """
        session_map = get_session_map()
        session_key = request.session.session_key
        if self.logout_method:
            self.logout_method(request)
        else:
            logout(request)
        session_map.delete_by_django_session(session_key)


def get_response_from_data(request, xml_string):
    u"""
    Получить утверждение-ответ из xml-строки.
    Используется для определения объекта в сервисе ACS.

    :param request: запрос, в рамках которого выполняется действие
    :type request: django.http.HttpRequest
    :param basestring xml_string: xml-строка, содержащая утверждение
    :return: объект Response, преобразованный из xml-строки
    :rtype: либо LogoutResponse, либо AuthResponse
    """
    config = settings.SSO_CONFIG or DEFAULT_SSO_CONFIG
    if config.get('zipping', False):
        assertion_str = decode_base64_and_inflate(xml_string)
    else:
        assertion_str = decode_base64(xml_string)
    assertion = xml_to_assertion(assertion_str)
    if is_logout_response(assertion):
        response = LogoutResponse(request)
        response.from_assertion(assertion)
        return response
    else:
        response = AuthResponse(request)
        response.from_assertion(assertion)
        return response


def get_request_from_data(request, xml_string):
    u"""
    Получить утверждение-запрос из xml-строки.
    Используется для определения объекта в сервисе ACS.

    :param request: запрос, в рамках которого выполняется действие
    :type request: django.http.HttpRequest
    :param xml_string: xml-строка, содержащая утверждение
    :type xml_string: basestring
    :return: объект Request, преобразованный из xml-строки
    :rtype: LogoutRequest | None
    """
    config = settings.SSO_CONFIG or DEFAULT_SSO_CONFIG
    if config.get('zipping', False):
        assertion_str = decode_base64_and_inflate(xml_string)
    else:
        assertion_str = decode_base64(xml_string)
    assertion = xml_to_assertion(assertion_str)
    if is_logout_request(assertion):
        request = LogoutRequest(request)
        request.from_assertion(assertion)
        return request
    else:
        return None


def get_str_from_assertion(assertion):
    u"""
    Преобразовать утверждение в строку перекодированную и упакованную.

    :param assertion: Утверждение (Assertion, xml)
    :type assertion: etree.ElementTree
    :return: xml-строка, содержащая утверждение
    :rtype: basestring
    """
    xml_string = assertion_to_xml(assertion)
    assertion_str = deflate_and_base64_encode(xml_string)
    return assertion_str