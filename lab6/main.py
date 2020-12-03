# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START gae_python38_app]
from flask import Flask, render_template
import psycopg2
import os

app = Flask(__name__)

dbname = os.getenv('DB_NAME')
dbuser = os.getenv('DB_USER')
# "localhost"  # "pgnet"  # "172.18.0.2" # os.getenv('DB_HOST')
dbhost = os.getenv('DB_HOST')
dbpasswd = os.getenv('DB_PASSWORD')


@app.route('/', defaults={'u_path': ''}, methods=['GET'])
@app.route('/<path:u_path>', methods=['GET'])
def root(u_path):
    count_paths(str(u_path))
    return show_path()


def count_paths(u_path):
    sql = """INSERT INTO pathcount (path, count)
            VALUES (%s, 1)
            ON CONFLICT (path) DO UPDATE
            SET count = pathcount.count + 1
            RETURNING count;"""

    print(u_path)
    try:
        conn = psycopg2.connect(
            database=dbname, user=dbuser, host=dbhost, password=dbpasswd)
        cur = conn.cursor()
        cur.execute(sql, (u_path, ))
        conn.commit()
        cur.close()
        conn.close()
    except psycopg2.DatabaseError as e:
        print(e)
        print("I am unable to connect to the database.")


def show_path():
    sql = """SELECT path, count FROM pathcount ORDER BY path;"""
    data_return = None

    try:
        conn = psycopg2.connect(
            database=dbname, user=dbuser, host=dbhost, password=dbpasswd)
        cur = conn.cursor()
        cur.execute(sql)
        data_return = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()
    except psycopg2.DatabaseError as e:
        print(e)
        print("I am unable to connect to the database.")

    print(data_return)
    return render_template('index.html', data=data_return)


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
# [END gae_python38_app]
