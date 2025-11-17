FROM python:3.11-slim

# Packages required for psycopg2 and compilation
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Environment variables (override these in production)
ENV MAIL_USERNAME=yourmail@test.com
ENV MAIL_PASSWORD=testpass
ENV SECRET_KEY=SuperRandomStringToBeUsedForEncryption
ENV PYTHONIOENCODING=UTF-8

# Copy requirements first to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt

WORKDIR /app
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . /app

# Use Flask CLI instead of deprecated runserver
ENTRYPOINT ["flask", "run", "--host=0.0.0.0"]

