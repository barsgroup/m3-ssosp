from django.conf.urls.defaults import patterns, url, include

from django.contrib import admin
from views import default

admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),
    (r'^sso/', include('ssosp.urls')),
    url(r'^', default, name="default"),
)
