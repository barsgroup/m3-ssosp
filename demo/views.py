#coding:utf-8
from django.shortcuts import render_to_response
from django.contrib.auth.models import User
from django.conf import settings


def default(request):
    attributes = request.session.get('attributes', {})
    tv = {
        'user': request.user,
        'session': request.session,
        'idp_logout_url': None,
        'idp_login_url': None,
        'attributes': attributes,
    }
    return render_to_response('default.html', tv)


def get_or_create_user(userid, attributes):
    try:
        user = User.objects.get(username=userid)
    except User.DoesNotExist:
        user = User.objects.create_user(userid, userid)
    # возьмем первый попавшийся бэкенд
    user.backend = settings.AUTHENTICATION_BACKENDS[0]
    return user
