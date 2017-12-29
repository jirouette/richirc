#!/usr/bin/python3
#coding: utf8

import tornado.ioloop
import tornado.web
import tornado.websocket
import uuid
from mq import RedisMQ
import os
import json

HOST = os.environ.get('RICHIRC_DEFAULT_SERVER', 'chat.freenode.net')
PORT = int(os.environ.get('RICHIRC_DEFAULT_PORT', 6697))
NICKNAME = os.environ.get('RICHIRC_DEFAULT_NICKNAME', 'richirc_user1')
CHANNEL = os.environ.get('RICHIRC_DEFAULT_CHANNEL', '#richirc')

class WebBridge(RedisMQ):
    BRIDGE_NAME = 'web'

    def __init__(self):
        super().__init__(self.BRIDGE_NAME, self.invoke)

    def invoke(self, ID, method, *args, **kwargs):
        client = app.user_list.get(ID)
        if client and not method.startswith('_'):
            return getattr(client.irc, method)(*args, **kwargs)

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        data = dict(host=HOST,
                    port=PORT,
                    nickname=NICKNAME,
                    channel=CHANNEL)
        self.render("front/templates/index.html", **data)

class IRCProxyClient(object):
    def __init__(self, ID, callback):
        self.ID = ID
        self.bridge = WebBridge()
        self.callback = callback

    def __getattr__(self, method):
        def execute(*args, **kwargs):
            if method.startswith('on_'):
                self.callback(self.ID, method, *args, **kwargs)
            else:
                self.bridge.send(self.ID, method, *args, **kwargs)
        return execute

class IRCWebSocket(tornado.websocket.WebSocketHandler):
    def open(self):
        self.ID = str(uuid.uuid4())
        self.application.user_list[self.ID] = self
        self.irc = IRCProxyClient(self.ID, self.ws_send)
        print("[WS] Welcome", self.ID)

    def on_close(self):
        del self.application.user_list[self.ID]
        print("[WS] Bye", self.ID)

    def ws_send(self, ID, method, *args, **kwargs):
        payload = dict(method=method,
                       args=args,
                       kwargs=kwargs,
                       ID=ID,
                       source=WebBridge.BRIDGE_NAME)
        self.write_message(json.dumps(payload))

    def on_message(self, message):
        payload = json.loads(message)
        method = payload.get('method')
        args = payload.get('args', list())
        kwargs = payload.get('kwargs', dict())
        return getattr(self.irc, method)(*args, **kwargs)

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
