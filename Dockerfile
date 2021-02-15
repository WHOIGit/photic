FROM python:3.8

ARG HTTP_PROXY
ARG HTTPS_PROXY

ENV PYTHONUNBUFFERED 1
ENV HTTP_PROXY=${HTTP_PROXY}
ENV HTTPS_PROXY=${HTTPS_PROXY}

RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/

RUN if [ -n "$HTTPS_PROXY" ] ; then pip install -r requirements.txt --proxy ${HTTPS_PROXY}; else pip install -r requirements.txt ; fi 

COPY . /code/
