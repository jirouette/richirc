"use strict";

class RichIRC
{
	constructor(server, port, nickname)
	{
		this.write("<em>Welcome to <strong>RichText</strong> ! </em>");
		this.ws = new WebSocket(((window.location.protocol === "https:") ? "wss://" : "ws://") + window.location.host + "/irc");
		this.ws.onopen = () => this.onOpen(server, port, nickname);
		this.ws.onmessage = (e) => this.onData(e);
		document.getElementById('userform').addEventListener('submit', (e) => this.onSubmit(e));
	}

	write(message)
	{
		document.getElementById('chat').innerHTML += message + "<br />";
	}

	onOpen(server, port, nickname)
	{
		this.write("Connecting to <strong>"+server+":"+port+"</strong> as <em>"+nickname+"... ");
		let payload = {
			'method': 'newclient',
			'args': [server, port],
			'kwargs': {
				'tls': true,
				'tls_verify': false,
				//'nickname': nickname
			}
		};
		this.ws.send(JSON.stringify(payload));
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
