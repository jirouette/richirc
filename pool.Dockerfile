FROM python:3

ADD requirements.txt .

RUN pip install -r ./requirements.txt

ADD richirc/mq.py .
ADD richirc/pool.py .

CMD ["python", "-u", "./pool.py"]
