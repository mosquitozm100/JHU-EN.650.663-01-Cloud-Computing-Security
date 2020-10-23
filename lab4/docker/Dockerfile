FROM python
RUN mkdir /app
COPY main.py /app/
WORKDIR /app
RUN pip install flask
EXPOSE 8080
ENV FLASK_APP=main.py
CMD flask run --host=0.0.0.0 --port=8080