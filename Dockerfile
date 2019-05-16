FROM python:alpine3.9

ENV PYTHONUNBUFFERED=0

RUN pip install flask Flask-HTTPAuth

COPY main.py /opt/

EXPOSE 5000

ENTRYPOINT ["python3", "-u", "/opt/main.py"]
