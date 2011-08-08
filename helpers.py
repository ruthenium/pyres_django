# pyres import
from pyres import ResQ

# django framework import
from django.conf import settings

class ClosingIterator(object):
    def __init__(self, iterator, close_callback):
        self.iterator = iter(iterator)
        self.close_callback = close_callback

    def __iter__(self):
        return self

    def next(self):
        return self.iterator.next()

    def close(self):
        self.close_callback()

def get_pyres():
    return ResQ('%s:%d' % (getattr(settings, 'REDIS_HOST', 'localhost'),
        getattr(settings, 'REDIS_PORT', 6379)))
