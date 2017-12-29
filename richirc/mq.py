#!/usr/bin/python3
#coding: utf8

import json
import os
import time
from threading import Thread
from redis import StrictRedis as Redis

def _redis():
    return Redis(host=os.environ.get('REDIS_HOST', 'localhost'),
                 port=int(os.environ.get('REDIS_PORT', 6379)),
                 db=0)

def _redis_chan():
    return os.environ.get('RICHIRC_REDIS_BRIDGE_CHANNEL', 'richirc')

class RedisMQ(Thread):
    def __init__(self, name, callback):
        Thread.__init__(self)
        self.name = name
        self.callback = callback

    def run(self):
        pubsub = _redis().pubsub()
        pubsub.subscribe(_redis_chan())
        while True:
            message = pubsub.get_message()
            if message:
                self.parse_message(message)
            time.sleep(0.01)

    def parse_message(self, message):
        data = message.get('data')
        if type(data) is bytes:
            data = json.loads(data.decode('utf-8'))
            if data.get('source') != self.name:
                args = data.get('args', list())
                kwargs = data.get('kwargs', dict())
                method = data.get('method')
                ID = str(data.get('ID'))
                print(">> ["+ID+"]",method, args, kwargs)
                self.callback(ID, method, *args, **kwargs)

    def send(self, ID, method, *args, **kwargs):
        print("<< ["+ID+"]",method, args, kwargs)
        payload = dict(source=self.name,
                       method=method,
                       args=args,
                       kwargs=kwargs,
                       ID=ID)
        try:
            return _redis().publish(_redis_chan(), json.dumps(payload))
        except TypeError:
            pass
