FROM python:3

ADD requirements.txt .

RUN pip install -r ./requirements.txt

ADD richirc .

EXPOSE 1993

CMD ["python", "-u", "./web.py"]
