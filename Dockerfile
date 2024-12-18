# Use Python 3.12 as the base image
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./src ./src

RUN mkdir -p ./logs

ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

#WORKDIR /app/src
# TODO: Gunicorn & HTTPS
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 
