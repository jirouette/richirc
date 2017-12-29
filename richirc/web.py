#!/usr/bin/python3
#coding: utf8

import tornado.ioloop
import tornado.web
import tornado.websocket
import uuid
from mq import RedisMQ
import os
import json

METHOD_PREFIX = 'irc_'

HOST = os.environ.get('RICHIRC_DEFAULT_SERVER', 'chat.freenode.net')
PORT = int(os.environ.get('RICHIRC_DEFAULT_PORT', 6697))
NICKNAME = os.environ.get('RICHIRC_DEFAULT_NICKNAME', 'richirc_user1')
CHANNEL = os.environ.get('RICHIRC_DEFAULT_CHANNEL', '#richirc')

class WebBridge(RedisMQ):
    BRIDGE_NAME = 'web'

    def __init__(self):
        super().__init__(self.BRIDGE_NAME, self.invoke)

    def invoke(self, ID, method, *args, **kwargs):
        method = METHOD_PREFIX+method
        client = app.user_list.get(ID)
        if client and hasattr(client, method):
            return getattr(client, method)(*args, **kwargs)

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        data = dict(host=HOST,
                    port=PORT,
                    nickname=NICKNAME,
                    channel=CHANNEL)
        self.render("front/templates/index.html", **data)

class IRCWebSocket(tornado.websocket.WebSocketHandler):
    ## WS methods

    def open(self):
        self.ID = str(uuid.uuid4())
        self.application.user_list[self.ID] = self
        self.bridge = WebBridge()
        print("[WS] Welcome", self.ID)

    def on_message(self, message):
        payload = json.loads(message)
        method = payload.get('method')
        args = payload.get('args', list())
        kwargs = payload.get('kwargs', dict())
        self.send(method, *args, **kwargs)

    ## IRC methods

    def send(self, method, *args, **kwargs):
        self.bridge.send(self.ID, method, *args, **kwargs)

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

    def on_close(self):
        del self.application.user_list[self.ID]
        print("[WS] Bye", self.ID)

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/irc", IRCWebSocket),
        (r'/js/(.*)', tornado.web.StaticFileHandler, {'path': 'front/js'}),
    ])

if __name__ == "__main__":
    app = make_app()
    app.user_list = dict()
    app.listen(int(os.environ.get('RICHIRC_WEB_PORT', 1993)))
    WebBridge().start()
    print("[!] RichIRC web platform started")
    tornado.ioloop.IOLoop.current().start()
