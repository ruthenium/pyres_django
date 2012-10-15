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
 2. Checkout the app code to your project path:
    ```git clone git://github.com/ruthenium/pyres_django.git```
 3. Add 'pyres_django' to your INSTALLED_APPS.
 4. If needed, set the REDIS_HOST and REDIS_PORT config settings.

And that's it! Now everything should work.

## System requirements

 1. [Redis](http://redis.io/) server.
 2. [Pyres](https://github.com/binarydud/pyres) and its dependencies.
 3. [Django](https://www.djangoproject.com/) 1.3 or higher (because of class-based views in the web ui).
 4. [Pyres-Scheduler](https://github.com/c-oreills/pyres-scheduler) 2.0.3

## USAGE

### Adding job to a queue:

In your `urls.py` add:

    import pyres_django
    pyres_django.autodiscover()

Adding this will autodiscover all periodic jobs to be executed.

### Adding a periodic job to a queue:

Create a `tasks.py` file inside your app folder. Add a class strating with `Periodic`, add a `perform()` function and a __queue__ attribute as stated in [pyres](http://itybits.com/pyres/example.html). You should also add a `run every` for adding cron-like functionality as described in [APScheduler](http://packages.python.org/APScheduler/cronschedule.html).
Lets take an example.

    class IntervalMyJob(object):
        queue = "high"
        run_every = {'second': 2}

        @staticmethod
        def perform(args):
            print 'This will be seen every 2 seconds: %s' % args

and 

    class PeriodicMyJob(object):
        queue = "high"
        # Schedule a backup to run once from Monday to Friday at 5:30 (am)
        run_every = {'month': '6-8,11-12', 'day': '3rd fri', 'hour': '0-3'}

        @staticmethod
        def perform():
            print 'This will be seen every once from Monday to Friday at 5:30 (am)'

### Adding a one time job to a queue:

Import the get_pyres helper:

```from pyres_django import get_pyres```

Then anywhere in your code just do:

```get_pyres().enqueue(SomeJob, *some_args)```

### Starting pyres worker:

Just type into your console:

```$ QUEUES=q1,q2 python2 manage.py pyres_worker```

And worker should run.
If you would like to permanently define a queues list for it, you can set the PYRES_QUEUES variable in your settings.py.

### Web Interface:

Include pyres_django's urls.py as you usually do in your global urls.py:

```urlpatterns = patterns('', url('^my-prefix/', include('pyres_django.urls')), )```

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
 * [https://github.com/c-oreills](https://github.com/c-oreills) - the author of the [pyres-scheduler](https://github.com/c-oreills/pyres-scheduler)