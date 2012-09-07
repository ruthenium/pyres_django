# core imports:
import logging
from os import environ
from optparse import make_option

# django framework imports:
from django.conf import settings
from django.core.management.base import CommandError, NoArgsCommand

# pyres imports:
from pyres import setup_logging
from pyres.worker import Worker

class Command(NoArgsCommand):
    help = ('Runs pyres worker for queues specified in the PYRES_QUEUES '
            'settings variable or, if not present, specified in the '
            'QUEUE or QUEUES environment variables.')

    option_list = NoArgsCommand.option_list + (
        make_option('-i', '--interval', action='store', dest='interval',
            default=5, help='Worker polling interval. Defaults to 5 '
            'seconds'),

        make_option('-l', '--log-level', action='store',
            dest='log_level', default='info', help='Worker log level. Valid '
            'values are: "debug", "info", "warning", "error", '
            '"critical", in decreasing order of verbosity. Defaults '
            'to "info" if parameter not specified.'),

        make_option('-f', '--file', dest='log_file', help='If present, '
            'a log file will be used.'),
        )

    def handle_noargs(self, **options):

        queues = (environ.get('QUEUES') or environ.get('QUEUE') or
                getattr(settings, 'PYRES_QUEUES', None))

        if not queues:
            raise CommandError('A list of queues should be specified for '
                    'worker to run. Try set PYRES_QUEUES django settings '
                    'variable or QUEUES environment variable, e.g.\n'
                    '$ QUEUES=q1,q2 python2 management.py pyres_worker')
        if isinstance(queues, basestring):
            queues = queues.split(',')

        server = "%s:%d" % (getattr(settings, 'REDIS_HOST',
            'localhost'), getattr(settings, 'REDIS_PORT', 6379))

        try:
            interval = int(options.get('interval'))
        except ValueError:
            raise CommandError('Interval must be an integer')

        log_level = getattr(logging, options.get('log_level').upper(),
                'INFO')
        setup_logging("pyres", log_level=log_level,
                filename=options.get('log_file'))

        Worker.run(queues, server, interval)
