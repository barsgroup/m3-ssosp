#coding:utf-8
u"""
Регистрация обработчиков url-адресов для django.

Регистрируются адреса:

* acs - ssosp.views.sso_acs
* login - ssosp.views.sso_login
* logout - ssosp.views.sso_logout

"""
from __future__ import absolute_import
import django
if django.get_version() < '1.4':
   from django.conf.urls.defaults import patterns, url
else:
   from django.conf.urls import patterns, url
from ssosp.views import sso_acs, sso_login, sso_logout


urlpatterns = patterns('',
    url(r'^acs/$', sso_acs, name="acs"),
    url(r'^login/$', sso_login, name="login"),
    url(r'^logout/$', sso_logout, name="logout"),
)
