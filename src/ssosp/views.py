#coding:utf-8
from django.contrib.auth import get_user
from django.http import HttpResponse

from ssosp.request_response import get_request_from_data, LogoutRequest, AuthRequest, get_response_from_data, \
    LogoutResponse


def sso_acs(request):
    u"""
    Assertion Consumer Service
    Приемник ответов и запросов при взаимодействии для SSO посредством SAML 2.0
    """
    result = None
    # получим параметры пришедшего запроса
    next_url = request.POST.get('RelayState', None)
    response_data = request.POST.get('SAMLResponse', None)
    request_data = request.POST.get('SAMLRequest', None)
    if request_data:
        # пришел какой-то запрос
        req = get_request_from_data(request, request_data)
        if isinstance(req, LogoutRequest):
            # если это запрос на выход
            req.doLogoutBySession(request)
            result = HttpResponse()
        else:
            # неизвестный запрос
            raise Exception('Unknown request')
    elif response_data:
        # пришел какой-то ответ
        resp = get_response_from_data(request, response_data)
        if isinstance(resp, LogoutResponse):
            # если это ответ на выход
            result = resp.doLogout(request, next_url)
        else:
            # значит это ответ на вход
            result = resp.doLogin(request, next_url)
    else:
        # неизвестный запрос
        pass
    return result


def sso_login(request, next_url=None):
    u"""
    Подготовка запроса на Identity Provider для аутентификации
    """
    req = AuthRequest(request)
    if not next_url:
        next_url = request.GET.get('next', None)
    result = req.getLogin(next_url)
    return result


def sso_logout(request, next_url=None):
    u"""
    Подготовка запроса на Identity Provider для выхода из системы
    """
    req = LogoutRequest(request)
    user = get_user(request)
    if not next_url:
        next_url = request.GET.get('next', None)
    req.doLogout(request)
    result = req.getLogout(user.username, next_url)
    return result