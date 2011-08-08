# pyres imports:
from pyres import ResQ

# django framework imports:
from django.conf import settings

class WebContainer(object):
    '''
    Simple wrapper over dictinoaries,
    to pass to django templates.
    '''
    # TODO: perhaps it is better to use
    # a custom template tag to access a dict.
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

def redis_size(resq, key):
    rk = 'resque:'+key
    key_type = resq.redis.type(rk)
    item = 0
    if key_type == 'list':
        item = resq.redis.llen(rk)
    elif key_type == 'set':
        item = resq.redis.scard(rk)
    elif key_type == 'string':
        item = 1
    return item

def get_pyres():
    '''
    Connection getter.
    '''
    return ResQ('%s:%d' % (getattr(settings, 'REDIS_HOST', 'localhost'),
        getattr(settings, 'REDIS_PORT', 6379)))
