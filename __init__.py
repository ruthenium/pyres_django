from helpers import get_pyres
from pyres import ResQ
from pyres_scheduler import PyresScheduler


def autodiscover():
    """
    Auto-discover INSTALLED_APPS tasks.py modules and fail silently when
    not present. This forces an import on them to register any scheduled jobs they
    may want.
    """
    import imp
    from django.conf import settings

    for app in settings.INSTALLED_APPS:
        # For each app, we need to look for an tasks.py inside that app's
        # package. We can't use os.path here -- recall that modules may be
        # imported different ways (think zip files) -- so we need to get
        # the app's __path__ and look for cron.py on that path.

        # Step 1: find out the app's __path__ Import errors here will (and
        # should) bubble up, but a missing __path__ (which is legal, but weird)
        # fails silently -- apps that do weird things with __path__ might
        # need to roll their own cron registration.
        try:
            app_path = __import__(app, {}, {}, [app.split('.')[-1]]).__path__
        except AttributeError:
            continue

        # Step 2: use imp.find_module to find the app's admin.py. For some
        # reason imp.find_module raises ImportError if the app can't be found
        # but doesn't actually try to import the module. So skip this app if
        # its admin.py doesn't exist
        try:
            imp.find_module('tasks', app_path)
        except ImportError:
            continue

        # Step 3: import the app's task file. If this has errors we want them
        # to bubble up.
        modulename = __import__("%s.tasks" % app)

        # Step 4: iterate though tasks.py module and find all classes with their names
        # starting with 'Periodic' and 'Interval'.
        for item in dir(modulename.tasks):
            if 'Periodic' or 'Interval' in item and hasattr(item, '__class__'):
                pyres_sched = PyresScheduler()
                resque = ResQ()
                pyres_sched.add_resque(resque)
                pyres_sched.start()

                classname = getattr(modulename.tasks, item)
                if hasattr(classname, 'run_every'):
                    run_every = getattr(classname, 'run_every')

                if 'Periodic' in item:
                    print 'periodic'
                    pyres_sched.add_cron_job(classname, args=None, **run_every)
                elif 'Interval' in item:
                    pyres_sched.add_interval_job(classname, args=None, **run_every)

