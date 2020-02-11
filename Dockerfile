FROM python:3.6-slim-stretch
RUN mkdir /take-home
WORKDIR /take-home
COPY requirements.txt /take-home/
RUN pip install -r requirements.txt
COPY . /take-home/