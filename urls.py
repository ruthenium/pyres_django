from django.conf.urls.defaults import patterns, include, url
from django.shortcuts import redirect

urlpatterns = patterns('pyres_django.views',
    url(r'^/$', 'overview', name='resweb-index'),

    url(r'^working/$', 'working', name='resweb-working'),

    url(r'^queues/$', 'queues', name='resweb-queues'),
    url(r'^queues/(?P<queue_id>\w.+)/$', 'queue',
        name='resweb-queue'),
    url(r'^queues_delete/(?P<queue_id>\w.+)/$', 'delete_queue',
        name='resweb-queue-delete'),
    # Note: pyres currently doesn't support * for queues.

    url(r'^failed/$', 'failed', name='resweb-failed'),
    url(r'^failed/retry/$', 'failed_job', {'retry':True},
        name='resweb-failed-retry'),
    url(r'^failed/delete/$', 'failed_job', name='resweb-failed-delete'),

    url(r'^failed/delete_all/$', 'delete_all_failed',
        name='resweb-delete-all-failed'),
    url(r'^failed/retry_all/$', 'retry_failed',
        name='resweb-retry-all-failed'),

    url(r'^workers/$', 'workers', name='resweb-workers'),
    url(r'^workers/(?P<worker_id>\w.+)/$', 'worker',
        name='resweb-worker'),


    #url(r'^stats/$', 'stats', name='resweb-stats'),
    url(r'^stats/$', lambda r: redirect('resweb-stats-key',
        key='resque'), name='resweb-stats'),
    url(r'^stats/(?P<key>\w+)/$', 'stats', name='resweb-stats-key'),

    url(r'^stat/(?P<stat_id>\w.+)/$', 'stat', name='resweb-stat'),


    url(r'^delayed/$', 'delayed', name='resweb-delayed'),

    url(r'^delayed/(?P<timestamp>\w.+)/$', 'delayed_timestamp',
        name='resweb-delayed-timestamp'),
)
