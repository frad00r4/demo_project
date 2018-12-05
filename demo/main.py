# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import signal
import sys

from twisted.internet import reactor


def signal_handler(sig, frame):
    reactor.stop()


def runner(config):
    if config.get('mode') not in ('client', 'worker', 'dispatcher'):
        print('"mode" field is required')
        return 3

    module = __import__('demo.modules.%s' % config.get('mode'), globals(), locals(), [b'initial', b'report'], -1)
    module.initial(config)

    signal.signal(signal.SIGINT, signal_handler)

    reactor.run()

    try:
        module.report()
    except AttributeError:
        pass

    return 0
