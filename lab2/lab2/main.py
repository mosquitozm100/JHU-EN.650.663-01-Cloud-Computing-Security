from flask import Flask, json, jsonify, render_template, request, url_for, redirect, session, escape
from google.cloud import datastore
import os
from werkzeug.debug import DebuggedApplication

# If `entrypoint` is not defined in app.yaml, App Engine will look for an app
# called `app` in `main.py`.
app = Flask(__name__)

# Set the secret key to some random bytes. Keep this really secret!
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

if app.debug:
    app.wsgi_app = DebuggedApplication(app.wsgi_app, evalex=True)


DS = datastore.Client()  # The client to connect with Google cloud storage
EVENT = 'Event'  # Name of the event table, can be anything you like.
ROOT = DS.key('Entities', 'root')  # Name of root key, can be anything.

# Distinguish between data for local server and cloud server
if os.getenv('GAE_ENV', '').startswith('standard'):
    ROOT = DS.key('Entities', 'root')
else:
    ROOT = DS.key('Entities', 'dev')


def encrypt_pswd(pswdStr, hash):
    if hash == None:
        hash = bcrypt.gensalt()
    return bcrypt.hashpw(pswdStr, hash)


def put_event(name, dateStr):
    '''
    Put a new event into google cloud storage datebase.
    Args:
        name - the name of new event
        dataStr - the date of the new event in string form.

    Returns:
        null
    '''
    entity = datastore.Entity(key=DS.key(EVENT, parent=ROOT))
    entity.update({'name': name, 'date': dateStr})
    DS.put(entity)


def request_parse(req_data):
    '''
    A helper function to get name and date from json file in Get/Post method.
    Args:
        req_data - the json containing name and date
    Returns:
        the name and date contains in the json
    '''
    if req_data.method == 'POST':
        data = req_data.json
    elif req_data.method == 'GET':
        data = req_data.args
    return data


def createSession(username):
    session.create(username)
    return 'yes'


@app.route('/')
@app.route('/index.html')
def root():
    '''
    Direct these two request to the index.html page.
    '''
    print(session)
    if 'username' in session:
        return app.send_static_file('index.html')
    else:
        login_url = url_for('login')
        return redirect(login_url)


@app.route('/events', methods=['GET'])
def events():
    '''
    Get all events stored in the google cloud database.
    Returns:
        id, name and date for all events in json
    '''
    events = []
    for val in DS.query(kind=EVENT, ancestor=ROOT).fetch():
        val['id'] = val.id
        events.append(val)
    jsonEvents = {}
    jsonEvents["events"] = events
    return jsonify(jsonEvents)


@app.route('/event', methods=['POST'])
def event():
    '''
    Add a new event into google cloud storage datebase.
    Returns:
        Success.
    '''
    data = request_parse(request)
    nameStr = data.get("name")
    dateStr = data.get("date")
    put_event(nameStr, dateStr)
    return 'Create successfully'


@app.route('/event/<int:event_id>', methods=['DELETE'])
def delete(event_id):
    '''
    Delete the event with input event_id from google cloud storage
    Args:
        event_id - the id of the event about to delete.
    Returns:
        Delete Success - 'Delete successfully.'
        Delete Fails - Error! Event not found!'
    '''
    deleteKey = DS.key(EVENT, event_id, parent=ROOT)
    try:
        event = DS.get(deleteKey)
        DS.delete(event.key)
    except:
        return 'Error! Event not found!'
    else:
        return 'Delete successfully.'


@app.route('/login', methods=['GET', 'POST'])
def login():
    print(session)
    if request.method == 'GET':
        return app.send_static_file('login.html')
    elif request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode()
        print(username)
        print(password)
        user_key = DS.key('Users', username)
        users = DS.query(kind='Users', ancestor=user_key)
        for user in list(users):
            if user['username'] == username and user['password'] == encrypt_pswd(password, user['password']):
                createSession(username)
                return app.send_static_file('index.html')
            else:
                return 'Error!'
        return redirect(url_for('root'))


@app.route('/signup')
def signup():
    return app.send_static_file('signup.html')


@app.route('/logout')
def logout():
    # remove the username from the session if it is there
    print(session)
    session.pop('username', None)
    return redirect(url_for('root'))


if __name__ == '__main__':
    '''
    Run the server for local test.
    '''
    app.run(host='127.0.0.1', port=8080, debug=True)
