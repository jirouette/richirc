build:
	sudo docker-compose build
run: build
	sudo docker-compose up
start: build
	sudo docker-compose start
stop:
	sudo docker-compose stop
