# pull the official base image
FROM python:3.11

WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1


# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt /app
RUN pip3 install -r requirements.txt

# copy project
COPY . /app

COPY start-server.sh /app/start-server.sh
RUN chmod +x /app/start-server.sh

EXPOSE 80
STOPSIGNAL SIGTERM
CMD ["sh", "./start-server.sh"]



