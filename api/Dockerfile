FROM python:3.10.7-slim-buster

RUN apt update --no-install-recommends -y
RUN apt install --no-install-recommends -y libpq-dev software-properties-common curl build-essential wget iputils-ping


COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Create App folder 
RUN mkdir /yet-another-api
WORKDIR /yet-another-api
# copy all files
COPY . /yet-another-api

#start server
CMD gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:${API_PORT}