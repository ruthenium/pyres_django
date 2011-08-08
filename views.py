# core imports:
from itertools import chain

# django framework imports:
from django.conf import settings
from django.http import HttpResponse, Http404

# resweb imports
from resweb import server
from itty import handle_request

# project imports:
from pyres_django.helpers import ClosingIterator, get_pyres

server.HOST = get_pyres()

# XXX
# IMPORTANT!
# Note that according to current implementation of itty and resweb,
# the code below will not work without any patches to these libraries.
# XXX

def smart_auth(func):
    check_fn = lambda r: r.user.is_active and r.user.is_staff

    def wrapper(callback, check_fn):
        def view(request, *args, **kwargs):
            if check_fn(request):
                return callback(request, *args, **kwargs)
            raise Http404
        return view

    if getattr(settings, 'PYRES_PROTECT', False):
        return wrapper(func,
                getattr(settings, 'PYRES_PROTECT_WITH', check_fn))
    return func

@smart_auth
def resweb_view(request, path=None):
    # This view is based on the logic from 
    # the django_wsgi and twod-wsgi projects.
    # Thanks a lot to their respective authors for it!
    environ = request.environ

    script_name = environ['SCRIPT_NAME']

    if not path:
        path = r'/'
        script_name += environ['PATH_INFO']
    else:
        script_name += (environ['PATH_INFO'][:-len(path)])

    environ['SCRIPT_NAME'] = script_name.rstrip('/')
    environ['PATH_INFO'] = (path if path.startswith('/') else '/' + path)

    #if request.user.is_authenticated():
    #    environ['REMOTE_USER'] = request.user.username

    results = {}
    buffer = []
    def start_response(status, response_headers, exc_info=None):
        if exc_info is not None:
            raise exc_info[0], exc_info[1], exc_info[2]
        results["status"] = status
        results["response_headers"] = response_headers
        return buffer.append
    response = itty.handle_request(environ, start_response)
    while not results:
        buffer.append(response.next())
    response_iter = chain(buffer, response)
    if hasattr(response, "close"):
        response_iter = ClosingIterator(response_iter, response.close)
    response = HttpResponse(response_iter, status=int(results["status"].split()[0]))
    for header, value in results["response_headers"]:
        response[header] = value
    return response
