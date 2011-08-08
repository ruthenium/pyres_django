Pyres-django
============

## About
[Pyres](https://github.com/binarydud/pyres) is an excellent attempt of porting the [Resque](http://github.com/defunkt/resque) job queue to python.
**Pyres-django** aims to be just a small collection of helpers for simple integration of pyres to [django](https://www.djangoproject.com/).

## IMPORTANT

Pyres-django is yet unstable and perhaps not completely production-ready solution.
Basically, this is just a set of my own shortcuts moved to a separate django application.

## INSTALLATION

 1. Ensure that Pyres is installed and working.
 2. Add 'pyres_django' to your INSTALLED_APPS
 3. If needed, set the REDIS_HOST and REDIS_PORT config settings.

And that's it! Now everything should work.

## System requirements

 1. [Redis](http://redis.io/) server.
 2. [Pyres](https://github.com/binarydud/pyres) and its dependencies.
 3. [Django](https://www.djangoproject.com/) 1.3 or higher (because of class-based views in the web ui).

## USAGE

### Adding job to a queue:

Anywhere in your code just do:

```from pyres_django import get_pyres
get_pyres().enqueue(SomeJob, *some_args)```

### Starting pyres worker:

Just type into your console:

```$ QUEUES=q1,q2 python2 manage.py pyres_worker```

And worker should run.
If you would like to permanently define a queues list for it, you can set the PYRES_QUEUES variable in your settings.py.

### Web Interface:

In your global urls.py just add the following:

```urlpatterns = patterns('',
   url('^my-prefix', include('pyres_django.urls')),
)```

And now it will be available under your specified prefix.

## NOTE

According to the current implementation of the original ResWeb, It is not possible to use it
under django without any patches. So I've had to re-implement the resweb-functionality my own way.
It is still a "quick-and-dirty" solution, and I don't plan to develop it further, because the API of
pyres is still not stablized and the ability of wsgi-integration of course will present in future versions.

Although, the basic implementation of a "True-way" wsgi integration can be found in the "wsgi" branch of this app.

## Thanks to:

 * [binarydud](https://github.com/binarydud/) - an author of original pyres and resweb.
 * [alex](https://github.com/alex) - an author of the [django-wsgi](https://github.com/alex/django-wsgi)
 * [2degrees](https://github.com/2degrees) - the authors of the [twod.wsgi](https://github.com/2degrees/twod.wsgi)
