from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room, emit
import string, random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'replace-this-with-a-secret'
socketio = SocketIO(app, cors_allowed_origins='*')

# In-memory store: room_code -> text
rooms = {}

def gen_code(n=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create')
def create():
    code = gen_code(6)
    rooms[code] = ''
    return redirect(url_for('room', code=code))

@app.route('/join', methods=['POST'])
def join_post():
    code = request.form.get('code', '').strip().upper()
    if not code:
        return redirect(url_for('index'))
    # Create room if missing (optional)
    rooms.setdefault(code, '')
    return redirect(url_for('room', code=code))

@app.route('/room/<code>')
def room(code):
    code = code.strip().upper()
    rooms.setdefault(code, '')
    return render_template('room.html', code=code)

# --- Socket events ---
@socketio.on('join')
def on_join(data):
    room = data.get('room')
    if not room:
        return
    join_room(room)
    # send current content to the joining client only
    emit('init', {'text': rooms.get(room, '')}, to=request.sid)

@socketio.on('text_change')
def on_text_change(data):
    room = data.get('room')
    text = data.get('text', '')
    if not room:
        return
    rooms[room] = text
    # broadcast to everyone in room except the sender
    emit('text_change', {'text': text}, room=room, include_self=False)

if __name__ == '__main__':
    # For local dev: socketio.run(app)
    socketio.run(app, host='0.0.0.0', port=5000)