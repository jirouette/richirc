#!/usr/bin/python3
#coding: utf8

import pydle
import json
import os
import time
from threading import Thread
from redis import StrictRedis as Redis

class WebBridge(Thread):
    BRIDGE_NAME = 'pool'

    def __init__(self, pool):
        Thread.__init__(self)
        self.pool = pool
        if not hasattr(self.pool, 'client_list'):
            self.pool.client_list = dict()

    def run(self):
        r = Redis(host=os.environ.get('REDIS_HOST', 'localhost'),
                  port=int(os.environ.get('REDIS_PORT', 6379)),
                  db=0)
        pubsub_chan = os.environ.get('RICHIRC_REDIS_BRIDGE_CHANNEL', 'richirc')
        pubsub = r.pubsub()
        pubsub.subscribe(pubsub_chan)
        while True:
            message = pubsub.get_message()
            if message:
                self.parse_message(message)
            time.sleep(0.01)

    def parse_message(self, message):
        data = message.get('data')
        if type(data) is bytes:
            data = json.loads(data.decode('utf-8'))
            print(data)
            if data.get('source') != self.BRIDGE_NAME:
                args = data.get('args', list())
                kwargs = data.get('kwargs', dict())
                method = data.get('method')
                ID = str(data.get('ID'))
                if method == 'newclient':
                    self.newclient(ID, *args, **kwargs)
                elif not method.startswith('on_') and method != 'bridge':
                    self.invoke(ID, method, *args, **kwargs)

    def newclient(self, ID, *args, **kwargs):
        client = RichIRCClient("richirc_user1", realname=ID)
        client.ID = ID
        self.pool.connect(client, *args, **kwargs)
        self.pool.client_list[ID] = client
        print("connecting")

    def invoke(self, ID, method, *args, **kwargs):
        client = self.pool.client_list.get(ID)
        if client and hasattr(client, method):
            return getattr(client, method)(*args, **kwargs)

class RichIRCClient(pydle.Client):
    def on_connect(self):
        print("on_connect")
        for chan in os.environ.get('CHANNELS', '#richirc').split():
            self.join(chan)
        self.bridge('on_connect')

    def on_message(self, source, target, message):
        self.bridge('on_message', source, target, message)

    def bridge(self, method, *args, **kwargs):
        r = Redis(host=os.environ.get('REDIS_HOST', 'localhost'),
                  port=int(os.environ.get('REDIS_PORT', 6379)),
                  db=0)
        pubsub_chan = os.environ.get('RICHIRC_REDIS_BRIDGE_CHANNEL', 'richirc')
        payload = dict(source=WebBridge.BRIDGE_NAME,
                       method=method,
                       args=args,
                       kwargs=kwargs,
                       ID=self.ID)
        print("on_message", payload)
        return r.publish(pubsub_chan, json.dumps(payload))

if __name__ == '__main__':
    pool = pydle.ClientPool()
    WebBridge(pool).start()
    pool.handle_forever()
