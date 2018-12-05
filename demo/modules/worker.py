# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import random
import time

from twisted.internet import task
from twisted.internet.protocol import DatagramProtocol

from demo.main import reactor
from demo.proto import ProtocolParser


class WorkerProtocol(DatagramProtocol):
    def __init__(self, config):
        self.config = config
        self.dispatcher_address = (self.config['dispatcher_address'], self.config['dispatcher_port'])
        self.die = False
        self.die_time = None

    def datagramReceived(self, datagram, addr):
        if self.die is True:
            return

        proto = ProtocolParser.deserialize(datagram)
        print('Incoming request from %s %s' % addr)
        if proto.task_id is None or proto.task_worker_request is False:
            return
        waiting_time = random.randint(self.config['process_emulation_min'], self.config['process_emulation_max'])
        proto_answer = ProtocolParser(self.config['name'], {'task_worker_response': True}, proto.task_id)

        reactor.callLater(waiting_time, self.answer_receiver, proto_answer, addr)

    """
    Callback for emulation of job
    """
    def answer_receiver(self, proto, addr):
        if self.die is True:
            return

        print('Send answer to %s %s' % addr)
        self.transport.write(proto.serialize(), self.dispatcher_address)

    """
    Callback for watchdog process
    """
    def watchdog_callback(self, proto):
        if self.die is True:
            return

        print('Send watchdog')
        self.transport.write(proto.serialize(), self.dispatcher_address)

    """
    Callback for die process
    """
    def die_callback(self):
        # Back to live
        if self.die is True:
            if self.die_time + 60 < time.time():
                self.die = False
                print('Back to live')
            return

        # Check chance to die
        chance = random.randint(1, 100)
        if chance > self.config['die_chance']:
            return

        # Worker is die
        print('Die')
        self.die = True
        self.die_time = time.time()
        return


def initial(conf):
    # Prepare config
    config = {
        'name': 'worker_%i_%i' % (int(time.time()), random.randint(10, 1000)),
        'listen_port': 8001,
        'process_emulation_min': 5,
        'process_emulation_max': 10,
        'dispatcher_address': '127.0.0.1',
        'dispatcher_port': 8000,
        'die_chance': 25,
        'die_timeout': 60
    }
    config.update(conf)
    if config['die_chance'] > 75:
        print('Die chance more then 75, set to 25')
        config['die_chance'] = 25
    if config['die_timeout'] < 1:
        print('Die timeout less then 1, set to 60')
        config['die_timeout'] = 60

    worker_protocol = WorkerProtocol(config)
    worker_protocol.listening_port = reactor.listenUDP(config['listen_port'], worker_protocol)

    # Watchdog beat
    proto = ProtocolParser(config['name'], {})
    loop = task.LoopingCall(worker_protocol.watchdog_callback, proto)
    loop.start(5)

    # Die process
    loop = task.LoopingCall(worker_protocol.die_callback)
    loop.start(1)
