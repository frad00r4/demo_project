# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import ujson


class ProtocolParser(object):
    """
    if task_id is None it is watchdog packet
    """
    def __init__(self, codename, flags, task_id=None):
        self.codename = codename
        self.task_id = task_id
        self.task_client_request = flags.get('task_client_request', False)
        self.task_client_response = flags.get('task_client_response', False)
        self.task_worker_request = flags.get('task_worker_request', False)
        self.task_worker_response = flags.get('task_worker_response', False)

    def serialize(self):
        proto_data = {
            'codename': self.codename,
            'task_id': self.task_id,
            'flags': {
                'task_client_request': self.task_client_request,
                'task_client_response': self.task_client_response,
                'task_worker_request': self.task_worker_request,
                'task_worker_response': self.task_worker_response
            }
        }

        return ujson.dumps(proto_data)

    @classmethod
    def deserialize(cls, json):
        data = ujson.loads(json)
        return cls(**data)
