from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'chatapp_secret')
database_url = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chat.db'))
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins='*')

ROOMS = ['General', 'Tech', 'Random']

# Tracks who is online: { sid: { username, room } }
online_users = {}

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    room = db.Column(db.String(50))
    text = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html', rooms=ROOMS)

# --- Socket events ---

@socketio.on('join')
def on_join(data):
    username = data.get('username', 'Anonymous').strip() or 'Anonymous'
    room = data.get('room', 'General')
    if room not in ROOMS:
        room = 'General'

    online_users[request.sid] = {'username': username, 'room': room}
    join_room(room)

    # Send last 30 messages to the user who just joined
    history = Message.query.filter_by(room=room).order_by(Message.timestamp.desc()).limit(30).all()
    history_data = [
        {'username': m.username, 'text': m.text, 'timestamp': m.timestamp.strftime('%H:%M')}
        for m in reversed(history)
    ]
    emit('history', history_data)

    # Notify the room
    emit('system', {'text': f'{username} joined the room'}, to=room)

    # Broadcast updated user list to everyone in the room
    emit('user_list', get_room_users(room), to=room)

@socketio.on('message')
def on_message(data):
    user = online_users.get(request.sid)
    if not user:
        return
    username = user['username']
    room = user['room']
    text = data.get('text', '').strip()
    if not text:
        return

    # Save to database
    msg = Message(username=username, room=room, text=text)
    db.session.add(msg)
    db.session.commit()

    # Broadcast to everyone in the room
    emit('message', {
        'username': username,
        'text': text,
        'timestamp': msg.timestamp.strftime('%H:%M')
    }, to=room)

@socketio.on('typing')
def on_typing(data):
    user = online_users.get(request.sid)
    if not user:
        return
    emit('typing', {'username': user['username'], 'typing': data.get('typing', False)},
         to=user['room'], include_self=False)

@socketio.on('switch_room')
def on_switch_room(data):
    user = online_users.get(request.sid)
    if not user:
        return
    old_room = user['room']
    new_room = data.get('room', 'General')
    if new_room not in ROOMS or new_room == old_room:
        return

    leave_room(old_room)
    emit('system', {'text': f'{user["username"]} left the room'}, to=old_room)
    emit('user_list', get_room_users(old_room), to=old_room)

    user['room'] = new_room
    join_room(new_room)

    history = Message.query.filter_by(room=new_room).order_by(Message.timestamp.desc()).limit(30).all()
    history_data = [
        {'username': m.username, 'text': m.text, 'timestamp': m.timestamp.strftime('%H:%M')}
        for m in reversed(history)
    ]
    emit('history', history_data)
    emit('room_changed', {'room': new_room})
    emit('system', {'text': f'{user["username"]} joined the room'}, to=new_room)
    emit('user_list', get_room_users(new_room), to=new_room)

@socketio.on('disconnect')
def on_disconnect():
    user = online_users.pop(request.sid, None)
    if user:
        emit('system', {'text': f'{user["username"]} left the room'}, to=user['room'])
        emit('user_list', get_room_users(user['room']), to=user['room'])

def get_room_users(room):
    return [u['username'] for u in online_users.values() if u['room'] == room]

if __name__ == '__main__':
    socketio.run(app, debug=True)
