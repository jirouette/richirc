#!/usr/bin/python3
#coding: utf8

import pydle
from mq import RedisMQ
from functools import partial

class WebBridge(RedisMQ):
    BRIDGE_NAME = 'pool'

    def __init__(self):
        super().__init__(self.BRIDGE_NAME, self.invoke)

    def newclient(self, ID, *args, **kwargs):
        client = RichIRCClient(ID, self, *args, **kwargs)
        pool.client_list[ID] = client

    def invoke(self, ID, method, *args, **kwargs):
        if method == 'newclient':
            return self.newclient(ID, *args, **kwargs)

        client = pool.client_list.get(ID)
        if client and hasattr(client, method):
            if method == 'connect':
                return pool.connect(client, *args, **kwargs)
            return getattr(client, method)(*args, **kwargs)

class RichIRCClient(pydle.Client):
    def __init__(self, ID, bridge, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ID = ID
        self.bridge = bridge

        for attr in dir(self):
            if attr.startswith('on_'):
                setattr(self, attr, partial(self._on_event, attr))

    def _on_event(self, attr, *args, **kwargs):
        getattr(super(), attr)(*args, **kwargs)
        return self.send(attr, *args, **kwargs)

    def send(self, *args, **kwargs):
        self.bridge.send(self.ID, *args, **kwargs)

if __name__ == '__main__':
    pool = pydle.ClientPool()
    pool.client_list = dict()
    WebBridge().start()
    print("[!] RichIRC pool started")
    pool.handle_forever()
