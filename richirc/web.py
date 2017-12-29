#!/usr/bin/python3
#coding: utf8

import tornado.ioloop
import tornado.web
import tornado.websocket
import uuid
from pool import WebBridge as PoolWebBridge
from redis import StrictRedis as Redis
from threading import Thread
import os
import json
import time

METHOD_PREFIX = 'irc_'

class WebBridge(PoolWebBridge):
    BRIDGE_NAME = 'web'

    def __init__(self, application):
        Thread.__init__(self)
        self.application = application

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
                if method.startswith('on_'):
                    self.invoke(ID, METHOD_PREFIX+method, *args, **kwargs)

    def invoke(self, ID, method, *args, **kwargs):
        client = self.application.user_list.get(ID)
        if client and hasattr(client, method):
            return getattr(client, method)(*args, **kwargs)

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        data = dict(host=os.environ.get('RICHIRC_DEFAULT_SERVER',
                                        'chat.freenode.net'),
                    port=int(os.environ.get('RICHIRC_DEFAULT_PORT', 6697)),
                    nickname=os.environ.get('RICHIRC_DEFAULT_NICKNAME',
                                            'richirc_user1'),
                    channel=os.environ.get('RICHIRC_DEFAULT_CHANNEL',
                                           '#richirc')
                    )
        self.render("front/templates/index.html", **data)

class IRCWebSocket(tornado.websocket.WebSocketHandler):
    def open(self):
        self.ID = str(uuid.uuid4())
        self.application.user_list[self.ID] = self
        print("Welcome", self.ID)

    def on_message(self, message):
        payload = json.loads(message)
        method = payload.get('method')
        args = payload.get('args', list())
        kwargs = payload.get('kwargs', dict())
        self.bridge(method, *args, **kwargs)

    def irc_on_message(self, source, target, message):
        payload = dict(method='on_message',
                       source=source,
                       target=target,
                       message=message)
        self.write_message(json.dumps(payload))

    def irc_on_connect(self):
        payload = dict(method='on_connect')
        self.write_message(json.dumps(payload))

    def irc_on_join(self, channel, user):
        payload = dict(method='on_join',
                       channel=channel,
                       user=user)
        self.write_message(json.dumps(payload))

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
        return r.publish(pubsub_chan, json.dumps(payload))

    def on_close(self):
        print("Bye", self.ID)

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/irc", IRCWebSocket),
        (r'/js/(.*)', tornado.web.StaticFileHandler, {'path': 'front/js'}),
    ])

if __name__ == "__main__":
    app = make_app()
    app.user_list = dict()
    app.listen(1993)
    WebBridge(app).start()
    tornado.ioloop.IOLoop.current().start()
