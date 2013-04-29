#coding:utf-8
from django.conf.urls.defaults import patterns, url
from ssosp.views import sso_acs, sso_login, sso_logout


urlpatterns = patterns('',
    url(r'^acs$', sso_acs, name="acs"),
    url(r'^login/$', sso_login, name="login"),
    url(r'^logout/$', sso_logout, name="logout"),
)
