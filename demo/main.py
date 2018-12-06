# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import signal

from twisted.internet import reactor


# Add handler on Ctrl+C for report print
def signal_handler(sig, frame):
    # Stop reactor
    reactor.stop()


def runner(config):
    if config.get('mode') not in ('client', 'worker', 'dispatcher'):
        print('"mode" field is required')
        return 3

    # Load module
    module = __import__('demo.modules.%s' % config.get('mode'), globals(), locals(), [b'initial', b'report'], -1)

    # Initial module
    module.initial(config)

    # Set handler
    signal.signal(signal.SIGINT, signal_handler)

    # Start application
    reactor.run()

    # Print report if it exists
    try:
        module.report()
    except AttributeError:
        pass

    return 0
