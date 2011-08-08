from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('pyres_django.views',
    url(r'^(.+)?$', 'resweb_view'),
)
