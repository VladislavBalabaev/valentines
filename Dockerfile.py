FROM python:3.10.13-bullseye

WORKDIR /usr/src/app

RUN apt-get update
RUN apt-get install -y nano iputils-ping vim tmux

COPY requirements.txt ./
RUN python -m pip cache purge
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY bot ./bot/
COPY .env ./
