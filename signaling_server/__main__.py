# Basic Websocket signaling server
# My usecase requires only two clients to be connected at a time, so I'm not using rooms

from flask import Flask, render_template, render_template_string
from flask_socketio import SocketIO

app = Flask(__name__)
#app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
socketio = SocketIO(app, cors_allowed_origins='*')

@app.route('/')
def index():
    return render_template_string('Websocket server is running')

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')


@socketio.on('offer')
def handle_offer(data):
    print('Received offer')
    socketio.emit('offer', data, include_self=False)

@socketio.on('answer')
def handle_answer(data):
    print('Received answer')
    socketio.emit('answer', data,  include_self=False)

if __name__ == '__main__':
    print('Running on http://localhost:8080')
    socketio.run(app, port=8080)