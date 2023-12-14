FROM python:3.10-slim

RUN apt-get update && apt-get install -y git

WORKDIR /app
COPY . /app
RUN pip3 install --no-cache-dir -r requirements.txt
