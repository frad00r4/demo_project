# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import time
import random

from twisted.internet import task
from twisted.internet.protocol import DatagramProtocol

from demo.main import reactor
from demo.proto import ProtocolParser


tasks = {}
finished_tasks = {}


class ClientProtocol(DatagramProtocol):
    def __init__(self, config):
        self.config = config

    def callback(self):
        task_id = '%s_%i_%i' % (self.config['name'], int(time.time()), random.randint(10, 1000))
        proto = ProtocolParser(self.config['name'], {'task_client_request': True}, task_id)
        tasks[proto.task_id] = time.time()
        print('Send client request %s' % proto.task_id)
        self.transport.write(proto.serialize())

    def startProtocol(self):
        self.transport.connect(self.config['dispatcher_address'], self.config['dispatcher_port'])

    def stopProtocol(self):
        reactor.listenUDP(0, self)

    def datagramReceived(self, datagram, addr):
        proto = ProtocolParser.deserialize(datagram)
        print('Incoming request from %s %s' % addr)
        if proto.task_id is None or proto.task_client_response is False:
            print('Wrong packet')
            return None

        if tasks.get(proto.task_id):
            finished_tasks[proto.task_id] = time.time() - tasks[proto.task_id]
            tasks[proto.task_id] = True
            print('Incoming response %s. Work time is %.2f sec' % (proto.task_id, finished_tasks[proto.task_id]))
        else:
            print('Wrong task %s' % proto.task_id)


def initial(conf):
    # Prepare config
    config = {
        'name': 'client_%i_%i' % (int(time.time()), random.randint(10, 1000)),
        'dispatcher_address': '127.0.0.1',
        'dispatcher_port': 8000,
        'task_send_timeout': 60
    }
    config.update(conf)

    # Watchdog beat
    watchdog = ClientProtocol(config)
    reactor.listenUDP(0, watchdog)
    loop = task.LoopingCall(watchdog.callback)
    loop.start(config['task_send_timeout'])


def report():
    times = finished_tasks.values()
    average = sum(times) / len(times) if times else 0
    not_answered_tasks = len([i for i in tasks.values() if i is not True])

    print('Sent tasks: %d' % len(tasks))
    print('Finished tasks: %d' % len(finished_tasks))
    print('Not answered tasks: %d' % not_answered_tasks)
    print('Minimal task time: %.2f' % (min(times) if times else 0))
    print('Average task time: %.2f' % average)
    print('Maximal task time: %.2f' % (max(times) if times else 0))
