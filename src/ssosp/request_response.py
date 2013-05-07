#coding:utf-8
import urllib2
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import logout, login
from django.shortcuts import redirect
from django.utils.importlib import import_module
from ssosp.assertion_parser import xml_to_assertion, is_logout_request, get_session_from_request_assertion, \
    build_assertion, assertion_to_xml, is_logout_response, get_session_from_response_assertion, \
    get_userid_from_assertion, get_attributes_from_assertion, verify_assertion
from ssosp.utils import decode_base64_and_inflate, deflate_and_base64_encode, get_random_id, get_time_string


# Пример настроек в settings.py
# SSO_CONFIG = {
#     'idp': 'https://localhost:9443/samlsso',
#     'issuer': 'saml2.demo',
#     'index': '1537824998',
#     'acs': '/sso/acs/',
#     'session_map': 'ssosp.backends.db'
# }

DEFAULT_SSO_CONFIG = {
    'session_map': 'ssosp.backends.db',
    'signing': False,
}


class SSOException(Exception):
    pass


def get_session_map():
    config = settings.SSO_CONFIG or DEFAULT_SSO_CONFIG
    session_map_engine = config.get('session_map', None)
    engine = import_module(session_map_engine)
    return engine.SSOSessionMap()


def get_method(method_str):
    if method_str:
        module = '.'.join(method_str.split('.')[:-1])
        method = method_str.split('.')[-1]
        mod = import_module(module)
        return getattr(mod, method)
    else:
        return None


class SAMLObject(object):
    def __init__(self, request):
        self.config = settings.SSO_CONFIG or DEFAULT_SSO_CONFIG
        self.idp_url = self.config.get('idp', '')
        self.issuer = self.config.get('issuer', '')
        self.service_index = self.config.get('index', '')
        self.acs_url = request.build_absolute_uri(self.config.get('acs', ''))
        self.signing = self.config.get('signing', False)
        self.public_key_str = self.config.get('public_key', None)
        self.logout_method = get_method(self.config.get('logout', None))
        self.login_method = get_method(self.config.get('login', None))
        self.get_user_method = get_method(self.config.get('get_user', None))


class AuthResponse(SAMLObject):
    def __init__(self, request):
        super(AuthResponse, self).__init__(request)

    def fromAssertion(self, assertion):
        if self.signing and (not self.public_key_str or not verify_assertion(assertion, self.public_key_str)):
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

    def doLogin(self, request, next_url):
        if self.login_method:
            self.login_method(request, self.user)
        else:
            login(request, self.user)

        request.session['attributes'] = self.attributes
        # сохраним соответствие SSO-сессии и django-сессии
        if self.session_id:
            session_map = get_session_map()
            session_map.set_session_map(self.session_id, request.session.session_key)
        return redirect(next_url)


class LogoutResponse(SAMLObject):
    def __init__(self, request):
        super(LogoutResponse, self).__init__(request)

    def fromAssertion(self, assertion):
        if self.signing and (not self.public_key_str or not verify_assertion(assertion, self.public_key_str)):
            raise SSOException("Response not valid")

    def doLogout(self, request, next_url):
        session_map = get_session_map()
        session_key = request.session.session_key
        if self.logout_method:
            self.logout_method(request)
        else:
            logout(request)
        session_map.delete_by_django_session(session_key)
        return redirect(next_url)


class AuthRequest(SAMLObject):
    def __init__(self, request):
        super(AuthRequest, self).__init__(request)

    def getRequest(self):
        assertion_struct = {
            'tag': '{samlp}AuthnRequest',
            'attrs': {
                'AssertionConsumerServiceURL': self.acs_url,
                'Destination': self.idp_url,
                'ID': get_random_id(),
                'IssueInstant': get_time_string(),
                'ProtocolBinding': "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
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
            assertion_struct['attrs']['AttributeConsumingServiceIndex'] = self.service_index
        assertion = build_assertion(assertion_struct)
        req = get_str_from_assertion(assertion)
        return req

    def getLogin(self, next_url):
        request_str = self.getRequest()
        login_url = '%s?SAMLRequest=%s&RelayState=%s' % (self.idp_url, urllib2.quote(request_str),
                                                         urllib2.quote(next_url))
        return redirect(login_url)


class LogoutRequest(SAMLObject):
    def __init__(self, request):
        super(LogoutRequest, self).__init__(request)

    def fromAssertion(self, assertion):
        if self.signing and (not self.public_key_str or not verify_assertion(assertion, self.public_key_str)):
            raise SSOException("Response not valid")
        self.session_id = get_session_from_request_assertion(assertion)

    def doLogoutBySession(self, request):
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

    def getRequest(self, username):
        assertion_struct = {
            'tag': '{samlp}LogoutRequest',
            'attrs': {
                'AssertionConsumerServiceURL': self.acs_url,
                'ID': get_random_id(),
                'IssueInstant': get_time_string(),
                'ProtocolBinding': "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
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
        assertion = build_assertion(assertion_struct)
        req = get_str_from_assertion(assertion)
        return req

    def getLogout(self, username, next_url):
        request_str = self.getRequest(username)
        logout_url = '%s?SAMLRequest=%s&RelayState=%s' % (self.idp_url, urllib2.quote(request_str),
                                                          urllib2.quote(next_url))
        return redirect(logout_url)

    def doLogout(self, request):
        session_map = get_session_map()
        session_key = request.session.session_key
        if self.logout_method:
            self.logout_method(request)
        else:
            logout(request)
        session_map.delete_by_django_session(session_key)


def get_response_from_data(request, xml_string):
    assertion_str = decode_base64_and_inflate(xml_string)
    assertion = xml_to_assertion(assertion_str)
    if is_logout_response(assertion):
        response = LogoutResponse(request)
        response.fromAssertion(assertion)
        return response
    else:
        response = AuthResponse(request)
        response.fromAssertion(assertion)
        return response


def get_request_from_data(request, xml_string):
    assertion_str = decode_base64_and_inflate(xml_string)
    assertion = xml_to_assertion(assertion_str)
    if is_logout_request(assertion):
        request = LogoutRequest(request)
        request.fromAssertion(assertion)
        return request
    else:
        return None


def get_str_from_assertion(assertion):
    xml_string = assertion_to_xml(assertion)
    assertion_str = deflate_and_base64_encode(xml_string)
    return assertion_str