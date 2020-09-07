FROM python:3.8.5

WORKDIR /app

EXPOSE 8888

RUN apt-get update && apt-get install -y libxml2-dev libxmlsec1-dev libxmlsec1-openssl

COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY . ./
