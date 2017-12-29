FROM python:3

ADD requirements.txt .

RUN pip install -r ./requirements.txt

ADD richirc/web.py .

CMD ["python", "./web.py"]
