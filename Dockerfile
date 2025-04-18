FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV TZ=Europe/Rome

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    netcat-openbsd \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

COPY requirements.txt /app/
RUN pip install -r requirements.txt

COPY . /app/

COPY start-server.sh /app/
RUN chmod +x /app/start-server.sh

# Collect static files
RUN mkdir -p /app/static /app/media

# Expose port
EXPOSE 80

# Set the entrypoint
CMD ["./start-server.sh"]