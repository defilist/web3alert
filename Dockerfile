FROM python:3.10-slim

RUN apt-get update && apt-get install -y git

WORKDIR /app
COPY *.py requirements.txt hack /app/
RUN pip3 install --no-cache-dir -r requirements.txt
# RUN pipenv install --skip-lock
