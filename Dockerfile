FROM python:3
ADD . /data
WORKDIR /data
RUN pip install -r requirements/dev.txt
ENV FLASK_CONFIG dev_docker
