FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Use Pardisco PyPI mirror (fast inside Iran)
RUN pip config set global.index-url https://mirrors.pardisco.co/pip/simple/

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .