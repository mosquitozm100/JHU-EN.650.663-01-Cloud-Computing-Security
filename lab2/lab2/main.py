from flask import Flask, json, jsonify, render_template, request, url_for, redirect, session, escape, make_response, flash
from google.cloud import datastore
import os
import bcrypt
import datetime
from datetime import timedelta, timezone
from base64 import b64encode
import uuid
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
USERS = 'Users'
SESSION = 'Session'
ROOT = DS.key('Entities', 'root')  # Name of root key, can be anything.
USER_KEY = DS.key('Entities', 'root')


def encrypt_pswd(pswdStr, hash=None):
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
    # print("lalal")
    # print(USER_KEY)
    entity = datastore.Entity(key=DS.key(EVENT, parent=USER_KEY))
    entity.update({'name': name, 'date': dateStr})
    DS.put(entity)


def put_user(username, password):
    user_key = DS.key('Users', username)
    user = datastore.Entity(key=DS.key(USERS, parent=user_key))
    user.update({'username': username, 'password': password})
    DS.put(user)


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


def create_session(username):
    session_key = DS.key('Session', username)
    session = datastore.Entity(key=DS.key(SESSION, parent=session_key))
    random_secret_token = b64encode(os.urandom(64)).decode()

    expire_time = datetime.datetime.now() + datetime.timedelta(hours=1)

    session.update({'token': random_secret_token, 'expire_time': expire_time})
    DS.put(session)

    resp = make_response(app.send_static_file('index.html'))
    resp.set_cookie('user', username,
                    max_age=60*60, expires=expire_time)
    resp.set_cookie('token', random_secret_token,
                    max_age=60*60, expires=expire_time)
    return resp


def migrate_data(username):
    print(USER_KEY)
    for val in DS.query(kind=EVENT, ancestor=ROOT).fetch():
        deleteKey = DS.key(EVENT, val.id, parent=ROOT)
        DS.delete(deleteKey)
        put_event(val['name'], val['date'])


@ app.route('/')
@ app.route('/index.html')
def root():
    '''
    Direct these two request to the index.html page.
    '''
    username = request.cookies.get('user')
    token = request.cookies.get('token')
    if token == None:
        return redirect(url_for('login'))
    session_key = DS.key('Session', username)
    sessions = DS.query(kind=SESSION, ancestor=session_key).fetch()
    for session in sessions:
        if session['token'] == token:
            if session['expire_time'] > datetime.datetime.now(timezone.utc):
                return app.send_static_file('index.html')
            else:
                return redirect(url_for('logout'))
    else:
        return redirect(url_for('login'))


@ app.route('/events', methods=['GET'])
def events():
    '''
    Get all events stored in the google cloud database.
    Returns:
        id, name and date for all events in json
    '''
    events = []
    for val in DS.query(kind=EVENT, ancestor=USER_KEY).fetch():
        val['id'] = val.id
        events.append(val)
    jsonEvents = {}
    jsonEvents["events"] = events
    return jsonify(jsonEvents)


@ app.route('/event', methods=['POST'])
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


@ app.route('/event/<int:event_id>', methods=['DELETE'])
def delete(event_id):
    '''
    Delete the event with input event_id from google cloud storage
    Args:
        event_id - the id of the event about to delete.
    Returns:
        Delete Success - 'Delete successfully.'
        Delete Fails - Error! Event not found!'
    '''
    deleteKey = DS.key(EVENT, event_id, parent=USER_KEY)
    try:
        event = DS.get(deleteKey)
        DS.delete(event.key)
    except:
        return 'Error! Event not found!'
    else:
        return 'Delete successfully.'


@ app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return app.send_static_file('login.html')
    elif request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode()
        user_key = DS.key('Users', username)
        users = DS.query(kind='Users', ancestor=user_key).fetch()
        for user in list(users):
            if user['username'] == username and user['password'] == encrypt_pswd(password, user['password']):
                global USER_KEY
                USER_KEY = DS.key('Entities', username)
                return create_session(username)
        flash('Username and password not found!')
        return redirect(url_for('root'))


@ app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return app.send_static_file('signup.html')
    elif request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode()
        global USER_KEY
        USER_KEY = DS.key('Entities', username)
        put_user(username, encrypt_pswd(password))
        migrate_data(username)
        return create_session(username)


@ app.route('/logout')
def logout():
    # remove the username from the session if it is there
    username = request.cookies.get('user')
    token = request.cookies.get('token')
    if username == None:
        return redirect(url_for('root'))
    session_key = DS.key('Session', username)
    sessions = DS.query(kind=SESSION, ancestor=session_key).fetch()
    for session in sessions:
        if session['token'] == token:
            DS.delete(session.key)

    expired_time = datetime.datetime.now() - datetime.timedelta(hours=1)
    resp = make_response(redirect(url_for('root')))
    resp.set_cookie('user', '',
                    max_age=0, expires=expired_time)
    resp.set_cookie('token', '',
                    max_age=0, expires=expired_time)
    flash('You have signed out!')
    global USER_KEY
    USER_KEY = DS.key('Entities', 'root')
    return resp


if __name__ == '__main__':
    '''
    Run the server for local test.
    '''
    app.run(host='127.0.0.1', port=8080, debug=True)
