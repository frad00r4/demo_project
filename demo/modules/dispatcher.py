# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import time

from twisted.internet import task
from twisted.internet.protocol import DatagramProtocol
from six.moves import queue

from demo.main import reactor
from demo.proto import ProtocolParser


class DispatcherProtocol(DatagramProtocol):
    def __init__(self, config):
        self.config = config
        self.task_queue = queue.Queue()
        self.clients = {}
        self.workers = {}
        self.tasks = {}
        self.workers_list = []

    def datagramReceived(self, datagram, addr):
        proto = ProtocolParser.deserialize(datagram)

        # Watchdog update
        if proto.task_id is None or proto.task_worker_response is True:
            print('watchdog from worker %s:%s' % addr)
            if self.workers.get(proto.codename) is None:
                self.workers[proto.codename] = {
                    'last_check': None,
                    'address': addr,
                    'queue': []
                }
            self.workers[proto.codename]['last_check'] = time.time()

        # check client request and add new clients
        if proto.task_client_request is True:
            print('Request from client %s:%s' % addr)

            # Client update
            if self.clients.get(proto.codename) is None:
                self.clients[proto.codename] = {
                    'address': addr,
                    'tasks': []
                }

            try:
                self.task_queue.put_nowait(proto.task_id)
            except queue.Full:
                print('ERROR: Queue is full, dropped')
                return None

            self.clients[proto.codename]['tasks'].append(proto.task_id)
            self.tasks[proto.task_id] = proto.codename

        # check worker response
        if proto.task_worker_response is True:
            response_proto = ProtocolParser('dispatcher', {'task_client_response': True}, proto.task_id)

            if self.tasks.get(proto.task_id) is None:
                print('Wrong task id')
                return None

            client_data = self.clients[self.tasks[proto.task_id]]
            self.transport.write(response_proto.serialize(), client_data['address'])
            client_data['tasks'].remove(proto.task_id)
            self.tasks.pop(proto.task_id)

    def task_queue_callback(self):
        time_now = time.time()
        for worker_name, worker_data in self.workers.items():
            if time_now - worker_data['last_check'] > self.config['worker_timeout']:
                for task_id in worker_data['queue']:
                    try:
                        self.task_queue.put_nowait(task_id)
                    except queue.Full:
                        print('ERROR: Queue is full')
                self.workers.pop(worker_name)
                self.workers_list = self.workers.items()

        if len(self.workers) == 0:
            print('ERROR: There is not any workers')
            return None

        while True:
            try:
                task_id = self.task_queue.get_nowait()
            except queue.Empty:
                break

            if len(self.workers_list) == 0:
                self.workers_list = self.workers.items()
            worker_name, worker_data = self.workers_list.pop()

            print(worker_name)

            worker_proto = ProtocolParser('dispatcher', {'task_worker_request': True}, task_id)
            self.workers[worker_name]['queue'].append(task_id)
            self.transport.write(worker_proto.serialize(), self.workers[worker_name]['address'])


def initial(conf):
    config = {
        'listen_port': 8000,
        'worker_timeout': 30,
        'queue_loop_timeout': 1
    }
    config.update(conf)

    dispatcher = DispatcherProtocol(config)
    reactor.listenUDP(config['listen_port'], dispatcher)
    loop = task.LoopingCall(dispatcher.task_queue_callback)
    loop.start(config['queue_loop_timeout'])
