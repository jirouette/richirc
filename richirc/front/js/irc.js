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
		console.log(payload);
		switch(payload.method)
		{
			case "on_message":
				this.onMessage(payload.source, payload.target, payload.message);
				break;
			case "on_connect":
				this.onConnect();
				break;
			case "on_join":
				this.onJoin(payload.channel, payload.user);
				break;
		}
	}

	onConnect()
	{
		this.write("Now connected ! Now joining <strong>"+this.chan+"</strong>... ");
		let join_payload = {
			'method': 'join',
			'args': [this.chan]
		};
		this.send(join_payload);
	}

	onMessage(source, target, message)
	{
		let converter = new showdown.Converter();
		let html = converter.makeHtml(message).replace(/^<p>|<\/p>$/g, '');
		if (this.target == this.nickname)
			html = "<span class='is-primary'>"+html+"</span>";
		this.write("<strong>&lt;"+target+"&gt;</strong> "+html);
	}

	onJoin(chan, nick)
	{
		if (nick == this.nickname)
			this.write("Joined <strong>"+chan+"</strong>");
		else
			this.write("<strong>"+nick+"</strong> has joined <strong>"+chan+"</strong>");
	}

	onSubmit(e)
	{
		let el = document.getElementById('usertext');
		let payload = {'method': 'message', 'args': [this.chan, el.value]}
		this.ws.send(JSON.stringify(payload));
		this.onMessage(this.chan, this.nickname, el.value);
		el.value = "";

		e.preventDefault();
		return false;
	}
}
