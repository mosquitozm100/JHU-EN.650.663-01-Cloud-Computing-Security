FROM python:3.6
RUN mkdir /app
ADD . /app
WORKDIR /app
RUN pip install flask \
    Psycopg2
EXPOSE 8080
ENV DB_NAME="postgres"
ENV DB_USER="postgres"
ENV DB_HOST="pgnet"
ENV DB_PASSWORD="mysecret"
ENV FLASK_APP=main.py
CMD flask run --host=0.0.0.0 --port=8080