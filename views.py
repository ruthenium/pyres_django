# core imports
import datetime
from base64 import b64decode

# django framework imports
from django.conf import settings
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic.base import TemplateView
from django.http import Http404

# pyres imports
from pyres import ResQ, failure, __version__
from pyres.worker import Worker as Wrkr

# project imports
from pyres_django.helpers import (WebContainer, redis_size, get_pyres)

#########################################################################
#
#                  DECORATOR FOR AUTHENTICATION
#
#########################################################################

def smart_auth(view):
    '''
    Decorator for protecting views depending on settings.
    '''

    # Default check callable:
    check_fn = lambda r: r.user.is_active and r.user.is_staff

    def _view_wrapper(v, checker):
        '''
        Wrapper to construct protected view.
        Is returned by decorator.
        '''
        def _protected_view(request, *args, **kwargs):
            '''
            Protected view function.
            Replaces given view, if needed.
            Checks if a client has permission to view original.
            '''
            if checker(request):
                # client is permitted to view this page
                return v(request, *args, **kwargs)
            # Client does not pass the test
            raise Http404

        return _protected_view

    if getattr(settings, 'PYRES_PROTECT', False):
        # We should protect the view
        return _view_wrapper(view,
                getattr(settings, 'PYRES_PROTECT_WITH', check_fn))

    # we should not do anything, returning original
    return view

#########################################################################
#
#                       BASE CLASS FOR VIEWS
#
#########################################################################

class ReswebView(TemplateView):

    _items_per_page = 20

    ################### pyres methods: ###########################

    def version(self):
        return __version__

    def address(self):
        return '%s:%d' % (self.resq.host, self.resq.port)

    def page_range(self):
        size = self.size()
        items_per_page = self._items_per_page
        start = self._start
        if size < items_per_page:
            return []

        num_pages = size / items_per_page
        if size % items_per_page > 0:
            num_pages += 1

        pages = []
        for i in range(num_pages):
            inum = i * num_pages
            if inum == start:
                current = True
            else:
                current = False
            pages.append(WebContainer(current=current, start=inum,
                index=i+1))
        return pages

    def start(self):
        return self._start

    def end(self):
        return self._end

    def _get_keys(self):
        return ('version', 'address') + self._keys

    ################## django methods: #################################

    def get_context_data(self, **kwargs):
        context = super(ReswebView, self).get_context_data(**kwargs)
        for k in self._get_keys():
            context[k] = getattr(self, k)()
        return context

    @method_decorator(smart_auth)
    def dispatch(self, request, *args, **kwargs):
        self.resq = get_pyres()
        if getattr(self, '_paginated', False):
            start = request.GET.get('start', 0)
            try:
                start = int(start)
            except ValueError:
                start = 0
            self._start = start
            self._end = self._start + self._items_per_page
        return super(ReswebView, self).dispatch(request, *args, **kwargs)

#########################################################################
#
#                            Mix-Ins
#
#########################################################################

# Mixins are just for code shortening.

class WorkingMixin(object):

    def all_workers(self):
        return Wrkr.all(self.resq)

    def total_workers(self):
        return len(self.all_workers())

    def workers(self):
        workers = []
        for w in self.resq.working():
            data = w.processing()
            host, pid, queues = str(w).split(':')
            item = {'state':w.state(),
                    'host':host,
                    'pid':pid,
                    'w':w,
                    'queue':w.job().get('queue')}
            if 'queue' in data:
                item['data'] = True
                item['code'] = data['payload']['class']
                item['runat'] = datetime.datetime.fromtimestamp(float(data['run_at']))
            workers.append(WebContainer(**item))
        return workers

#########################################################################

class QueuesMixin(object):
    def queues(self):
        return [WebContainer(q=q, size=self.resq.size(q)) for q in
                sorted(self.resq.queues())]

    def fail_count(self):
        return failure.count(self.resq)


#########################################################################
#
#                       CLASS-BASED VIEWS
#
#########################################################################

class Overview(ReswebView, WorkingMixin, QueuesMixin):
    template_name = 'resweb/overview.html'
    _keys = ('queues', 'fail_count', 'workers', 'total_workers')

overview = Overview.as_view()

#########################################################################

class Working(ReswebView, WorkingMixin):
    template_name = 'resweb/working.html'
    _keys = ('workers', 'total_workers')

working = Working.as_view()

#########################################################################

class Queues(ReswebView, QueuesMixin):
    template_name = 'resweb/queues.html'
    _keys = ('queues', 'fail_count')

queues = Queues.as_view()

#########################################################################

class Queue(ReswebView, QueuesMixin):
    template_name = 'resweb/queue.html'
    _keys = ('queue', 'size', 'jobs', 'start', 'end', 'queues',
            'page_range')
    _paginated = True

    def jobs(self):
        return [WebContainer(cls=j['class'], args=','.join([''.join(str(x)) for x in j['args']])) for j in
                self.resq.peek(self.queue(), self._start, self._end)]

    def size(self):
        #return self.resq.size(self.kwargs['queue_id']) or 0
        return self.resq.size(self.queue()) or 0

    def queue(self):
        return self.kwargs['queue_id']

queue = Queue.as_view()

#########################################################################

class Failed(ReswebView):
    template_name = 'resweb/failed.html'
    _keys = ('start', 'end', 'failed_jobs', 'size', 'page_range')
    _paginated = True

    def failed_jobs(self):
        jobs = []
        for j in failure.all(self.resq, self._start, self._end):
            backtrace = j['backtrace']
            if isinstance(backtrace, list):
                j['backtrace'] = '\n'.join(backtrace)

            j['payload_class'] = j['payload']['class']
            j['payload_args'] = str(j['payload']['args'])[:1024]
            jobs.append(WebContainer(**j))
        return jobs

    def size(self):
        return failure.count(self.resq) or 0

failed = Failed.as_view()

#########################################################################

class Workers(ReswebView):
    template_name = 'resweb/workers.html'
    _keys = ('workers',)

    def workers(self):
        workers = []
        for w in Wrkr.all(self.resq):
            data = w.processing()
            host, pid, queues = str(w).split(':')
            item = {'state':w.state(),
                    'host':host,
                    'pid':pid,
                    'w':w,
                    'queues':queues.split(','),
                    'queue':w.job().get('queue')}
            if 'queue' in data:
                item['data'] = True
                item['code'] = data['payload']['class']
                item['runat'] = datetime.datetime.fromtimestamp(float(data['run_at']))
            workers.append(WebContainer(**item))
        return workers

workers = Workers.as_view()

#########################################################################

class Worker(ReswebView):
    template_name = 'resweb/worker.html'
    _keys = ('worker',)

    def worker(self):
        worker = Wrkr.find(self.kwargs['worker_id'], self.resq)
        if not worker:
            return None
        host, pid, queues = str(worker).split(':')
        queues = queues.split(',')
        worker.host = host
        worker.pid = pid
        worker.queues = queues
        return worker

worker = Worker.as_view()

#########################################################################

class Stats(ReswebView):
    template_name = 'resweb/stats.html'
    _keys = ('key', 'stats', 'key_title')

    def key(self):
        return self.kwargs['key']

    def stats(self):
        key = self.key()
        if key == 'resque':
            return [ WebContainer(key=k, value=v) for k,v in self.resq.info().items() ]
        if key == 'redis':
            return [ WebContainer(key=k, value=v) for k,v in self.resq.redis.info().iteritems() ]
        if key == 'keys':
            return [ WebContainer(key=k,
                type=self.resq.redis.type('resque:'+k),
                size=redis_size(self.resq, k)) for k in self.resq.keys() ]
        return []

    def key_title(self):
        # TODO
        # translation;
        # maybe to templates?..
        k = self.kwargs['key']
        if k == 'resque':
            return 'Pyres'
        if k == 'redis':
            return self.address()
        if k == 'keys':
            return 'Keys owned by Pyres'
        return k

stats = Stats.as_view()

#########################################################################

class Stat(ReswebView):
    template_name = 'resweb/stat.html'
    _keys = ('key', 'key_type', 'size', 'stat_items')

    def key(self):
        return self.kwargs['stat_id']

    def key_type(self):
        # return value seems str
        return self.resq.redis.type(self._rk())

    def _rk(self):
        return 'resque:' + self.kwargs['stat_id']

    def size(self):
        return redis_size(self.resq, self.kwargs['stat_id'])

    def stat_items(self):
        #kt = str(self.key_type())
        kt = self.key_type()
        redis_key = self._rk()
        if kt == 'list':
            return self.resq.redis.lrange(redis_key, 0, 20) or []
        if kt == 'set':
            return self.resq.redis.smembers(redis_key) or []
        if kt == 'string':
            return [self.resq.redis.get(redis_key)]
        return []

stat = Stat.as_view()

#########################################################################

class Delayed(ReswebView):
    template_name = 'resweb/delayed.html'
    _keys = ('size', 'jobs', 'start', 'end', 'page_range')
    _paginated = True

    def size(self):
        return self.resq.delayed_queue_schedule_size() or 0

    def jobs(self):
        return [WebContainer(timestamp=datetime.datetime.fromtimestamp(float(t)),
            size=self.resq.delayed_timestamp_size(t)) for t in
            self.resq.delayed_queue_peek(self._start, self._end)]

delayed = Delayed.as_view()

#########################################################################

class DelayedTimestamp(ReswebView):
    template_name = 'resweb/delayed_timestamp.html'
    _keys = ('start', 'end', 'jobs', 'size', 'timestamp', 'page_range')
    _paginated = True

    def jobs(self):
        return [WebContainer(cls=j['class'], args=j['args']) for j in
                self.resq.delayed_timestamp_peek(self.timestamp(),
                    self._start, self._end)]
        #jobs = []
        #for j in resq.delayed_timestamp_peek(timestamp, start, end):
        #    jobs.append(WebContainer(cls=j['class'], args=j['args']))
        #return jobs

    def size(self):
        return resq.delayed_timestamp_size(self.timestamp()) or 0

    def timestamp(self):
        return self.kwargs['timestamp']

delayed_timestamp = DelayedTimestamp.as_view()

#########################################################################
#
#                            SIMPLE VIEWS
#
#########################################################################

# These views always return a redirect, so I've decided not to use
# generics for them.

@smart_auth
@require_POST
def failed_job(request, retry=False):
    failed_job_ = request.POST['failed_job']
    job = b64decode(failed_job_)
    if retry:
        # post /failed/retry
        decoded = ResQ.decode(job)
        failure.retry(get_pyres(), decoded['queue'], job)
    else:
        # post /failed/delete
        failure.delete(get_pyres(), job)
    return redirect('resweb-failed')

#########################################################################

@smart_auth
def delete_all_failed(request):
    # get /failed/delete_all
    resq = get_pyres()
    resq.redis.rename('resque:failed', 'resque:failed-staging')
    resq.redis.delete('resque:failed-staging')
    return redirect('resweb-failed')

#########################################################################

@smart_auth
def retry_failed(request, number=5000):
    # get /failed/retry_all
    resq = get_pyres()
    failures = failure.all(resq, 0, number)
    for f in failures:
        j = b64decode(f['redis_value'])
        failure.retry(resq, f['queue'], j)
    return redirect('resweb-failed')

#########################################################################

@smart_auth
@require_POST
def delete_queue(request, queue_id):
    get_pyres().remove_queue(queue_id)
    return redirect('resweb-queues')
