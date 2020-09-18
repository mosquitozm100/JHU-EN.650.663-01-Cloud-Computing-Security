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
from flask import Flask, json, jsonify, render_template, request
from google.cloud import datastore
from werkzeug.debug import DebuggedApplication

# If `entrypoint` is not defined in app.yaml, App Engine will look for an app
# called `app` in `main.py`.
app = Flask(__name__)

if app.debug:
    app.wsgi_app = DebuggedApplication(app.wsgi_app, evalex=True)


DS = datastore.Client()
EVENT = 'Event' # Name of the event table, can be anything you like.
ROOT = DS.key('Entities', 'root') # Name of root key, can be anything.

def put_event(name, date_str):
    entity = datastore.Entity(key=DS.key(EVENT, parent=ROOT))
    entity.update({'name': name, 'date': date_str})
    DS.put(entity)

def request_parse(req_data):
    if req_data.method == 'POST':
        data = req_data.json
    elif req_data.method == 'GET':
        data = req_data.args
    return data


@app.route('/')
def root():
    #return render_template('index.html');
    return app.send_static_file('index.html')

@app.route('/events', methods= ['GET'])
def events():
    events = []
    for val in DS.query(kind=EVENT, ancestor=ROOT).fetch():
        #print(val)
        val['id']=val.id
        events.append(val)
    jsonEvents = {}
    jsonEvents["events"] = events
    return jsonify(jsonEvents);
    
@app.route('/event', methods= ['POST'])
def event():
    data = request_parse(request)
    nameStr = data.get("name")
    dateStr = data.get("date")
    put_event(nameStr, dateStr)
    return 'OK'

@app.route('/delete', methods= ['POST'])
def delete():
    data = request_parse(request)
    id = data.get("id")
    deleteKey = DS.key('Entities', 'root', 'Event', id)
    print(deleteKey)
    print(DS.get(deleteKey))
    DS.delete(deleteKey)
    return 'OK'

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
# [END gae_python38_app]
