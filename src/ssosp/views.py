#coding:utf-8
u"""
Обработчики адресов сервисов по-умолчанию
"""
from django.contrib.auth import get_user
from django.http import HttpResponse

from ssosp.request_response import get_request_from_data, LogoutRequest, \
    AuthRequest, get_response_from_data, LogoutResponse


def sso_acs(request):
    u"""
    Assertion Consumer Service

    Приемник ответов и запросов при взаимодействии для SSO посредством SAML 2.0

    :param request: входящий запрос
    :type request: django.http.HttpRequest
    :return: ответ на запрос - обычно редирект на адрес SSO или адрес
        переданный через POST-параметр "RelayState"
    :rtype: django.http.HttpResponseRedirect | django.http.HttpResponse
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
            req.do_logout_by_session(request)
            result = HttpResponse()
        else:
            # неизвестный запрос
            raise Exception('Unknown request')
    elif response_data:
        # пришел какой-то ответ
        resp = get_response_from_data(request, response_data)
        if isinstance(resp, LogoutResponse):
            # если это ответ на выход
            result = resp.do_logout(request, next_url)
        else:
            # значит это ответ на вход
            result = resp.do_login(request, next_url)
    else:
        # неизвестный запрос
        pass
    return result


def sso_login(request, next_url=None):
    u"""
    Подготовка запроса на Identity Provider для входа в систему

    :param request: входящий запрос
    :type request: django.http.HttpRequest
    :param basestring next_url: следующий адрес после обработки
    :return: ответ на запрос - обычно редирект на адрес SSO или адрес
        переданный next_url
    :rtype: django.http.HttpResponseRedirect
    """
    req = AuthRequest(request)
    if not next_url:
        next_url = request.GET.get('next', None)
    result = req.get_login(next_url)
    return result


def sso_logout(request, next_url=None):
    u"""
    Подготовка запроса на Identity Provider для выхода из системы

    :param request: входящий запрос
    :type request: django.http.HttpRequest
    :param basestring next_url: следующий адрес после обработки
    :return: ответ на запрос - обычно редирект на адрес SSO или адрес
        переданный next_url
    :rtype: django.http.HttpResponseRedirect
    """
    req = LogoutRequest(request)
    user = get_user(request)
    if not next_url:
        next_url = request.GET.get('next', None)
    req.do_logout(request)
    result = req.get_logout(user.username, next_url)
    return result