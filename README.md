# SynthChat

A real-time chat application built with Flask-SocketIO and WebSockets, featuring a synthwave aesthetic — perspective grid background, retro sun, neon pink and orange accents.

🔗 **[Live Demo](https://synthchat.onrender.com)**

## Features

- **Real-time messaging** — messages appear instantly via WebSockets, no page refresh
- **Multiple rooms** — General, Tech, Random with live room switching
- **Live user list** — updates instantly when users join or leave
- **Typing indicators** — shows when another user is transmitting
- **Message history** — last 30 messages loaded when joining a room
- **Synthwave UI** — Orbitron font, perspective grid, CSS sun, neon borders

## Tech Stack

- Python 3 / Flask
- Flask-SocketIO for WebSocket handling
- SQLite via Flask-SQLAlchemy (PostgreSQL in production)
- Socket.IO JS client
- Eventlet for async worker
- Deployed on Render

## How WebSockets Work Here

Unlike HTTP (request → response), WebSockets keep a persistent two-way connection open. This app uses these events:

| Event | Direction | Purpose |
|---|---|---|
| `join` | Client → Server | User enters a room |
| `message` | Client → Server | User sends a message |
| `typing` | Client → Server | User is typing |
| `switch_room` | Client → Server | User changes room |
| `history` | Server → Client | Last 30 messages on join |
| `user_list` | Server → All in room | Updated online list |
| `system` | Server → All in room | Join/leave notifications |

## Getting Started

### 1. Install dependencies

```bash
pip install flask flask-socketio flask-sqlalchemy eventlet
```

### 2. Run the app

```bash
python app.py
```

### 3. Open in browser

```
http://127.0.0.1:5000
```

Open a second tab with a different callsign to test real-time messaging.

## Project Structure

```
ChatApp/
├── app.py               # Flask app, SocketIO events, database models
├── Procfile             # Gunicorn + eventlet worker for deployment
├── requirements.txt     # Python dependencies
└── templates/
    └── index.html       # Full frontend — join screen, chat UI, Socket.IO client
```
