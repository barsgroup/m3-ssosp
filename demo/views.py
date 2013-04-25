#coding:utf-8
from django.shortcuts import render_to_response


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