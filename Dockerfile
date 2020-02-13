FROM python:3.6-slim-stretch
RUN mkdir /trendpulse
WORKDIR /trendpulse
COPY requirements.txt /trendpulse/
RUN pip install -r requirements.txt
COPY . /trendpulse/
