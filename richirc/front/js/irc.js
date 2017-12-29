"use strict";

class RichIRC
{
	constructor(server, port, nickname, chan)
	{
		this.server = server;
		this.port = port;
		this.nickname = nickname;
		this.chan = chan;

		this.write("<em>Welcome to <strong>RichIRC</strong> ! </em>");
		this.ws = new WebSocket(((window.location.protocol === "https:") ? "wss://" : "ws://") + window.location.host + "/irc");
		this.ws.onopen = () => this.onOpen(server, port, nickname);
		this.ws.onmessage = (e) => this.onData(e);
		document.getElementById('userform').addEventListener('submit', (e) => this.onSubmit(e));
	}

	write(message)
	{
		document.getElementById('chat').innerHTML += message + "<br />";
	}

	send(obj)
	{
		this.ws.send(JSON.stringify(obj));
	}

	onOpen(server, port, nickname)
	{
		this.write("Connecting to <strong>"+server+":"+port+"</strong> as <em>"+nickname+"... ");

		// initializing client
		let newclient_payload = {
			'method': 'newclient',
			'args': [nickname],
			'kwargs': {
				'realname': nickname
			}
		};
		this.send(newclient_payload);

		// connecting client
		let connect_payload = {
			'method': 'connect',
			'args': [server, port],
			'kwargs': {
				'tls': true,
				'tls_verify': false,
			}
		};
		this.send(connect_payload);
	}

	onData(event)
	{
		let payload = JSON.parse(event.data);
		switch(payload.method)
		{
			case "on_message":
				this.onMessage(payload.source, payload.target, payload.message);
				break;
			case "on_connect":
				this.onConnect();
		}
	}

	onConnect()
	{
		this.write("Now connected ! ");
	}

	onMessage(source, target, message)
	{
		let converter = new showdown.Converter();
		let html = converter.makeHtml(message).replace(/^<p>|<\/p>$/g, '');
		this.write("<strong>&lt;"+target+"&gt;</strong> "+html);
	}

	onSubmit(e)
	{
		let el = document.getElementById('usertext');
		let payload = {'method': 'message', 'args': ['#richirc', el.value]}
		this.ws.send(JSON.stringify(payload));
		this.onMessage('userinput', 'you', el.value);
		el.value = "";

		e.preventDefault();
		return false;
	}
}
