# app/Dockerfile

FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    ffmpeg libsm6 libxext6 \
    libmp3lame0 \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

WORKDIR /app/api

RUN pip install -r requirements.txt

EXPOSE 8000

WORKDIR /app/api 


ENTRYPOINT ["fastapi", "dev", "app.py", "--port=8000", "--host=0.0.0.0"]
