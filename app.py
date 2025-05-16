from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import random
import json
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")  # Allow all origins

# Game state
games = {}
WORDS = ['APPLE', 'BEACH', 'CLOUD', 'DREAM', 'EARTH', 'FLAME', 'GRASS', 'HEART', 
         'JUICE', 'KNIFE', 'LIGHT', 'MONEY', 'NIGHT', 'OCEAN', 'PEACE', 'QUEEN',
         'RADIO', 'SMILE', 'TIGER', 'UNITY', 'VOICE', 'WATER', 'YOUTH', 'ZEBRA']

class Game:
    def __init__(self):
        self.word = random.choice(WORDS)
        self.players = {}
        self.start_time = None
        self.game_duration = 300  # 5 minutes in seconds
        self.game_started = False

    def add_player(self, player_id, username):
        self.players[player_id] = {
            'username': username,
            'guesses': [],
            'score': 0,
            'current_word': random.choice(WORDS)  # Each player gets their own word
        }

    def start_game(self):
        self.game_started = True
        self.start_time = time.time()

    def make_guess(self, player_id, guess):
        if player_id not in self.players or not self.game_started:
            return False
        
        guess = guess.upper()
        if len(guess) != 5:
            return False

        result = []
        current_word = self.players[player_id]['current_word']
        
        for i, letter in enumerate(guess):
            if letter == current_word[i]:
                result.append('correct')  # Changed from 'green'
            elif letter in current_word:
                result.append('present')  # Changed from 'yellow'
            else:
                result.append('absent')   # Changed from 'gray'

        self.players[player_id]['guesses'].append({
            'word': guess,
            'result': result
        })

        if guess == current_word:
            self.players[player_id]['score'] += 1
            self.players[player_id]['current_word'] = random.choice(WORDS)
            return True

        return False

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def on_join(data):
    room = data['room']
    username = data['username']
    
    if room not in games:
        games[room] = Game()  # game_started will be False by default
    else:
        # If the room exists but has no players, reset the game state
        if len(games[room].players) == 0:
            games[room] = Game()
    
    join_room(room)
    games[room].add_player(request.sid, username)
    
    # Send initial game state to the new player
    emit('game_state', {
        'word_length': 5,
        'current_word': games[room].players[request.sid]['current_word'],
        'game_started': games[room].game_started
    }, room=request.sid)
    
    # Broadcast updated player list to all players
    emit('players_update', {
        'players': {pid: {'username': p['username'], 'score': p['score']} 
                   for pid, p in games[room].players.items()}
    }, room=room)

@socketio.on('start_game')
def on_start_game(data):
    room = data['room']
    if room in games:
        games[room].start_game()
        emit('game_started', {
            'start_time': games[room].start_time
        }, room=room)

@socketio.on('guess')
def on_guess(data):
    room = data['room']
    guess = data['guess']
    
    if room in games:
        success = games[room].make_guess(request.sid, guess)
        if request.sid in games[room].players:
            result = games[room].players[request.sid]['guesses'][-1]['result']
            
            # Only send the result to the player who made the guess
            emit('guess_result', {
                'guess': guess,
                'result': result,
                'success': success,
                'new_word': games[room].players[request.sid]['current_word'] if success else None
            }, room=request.sid)
            
            # Broadcast updated scores to all players
            emit('scores_update', {
                'players': {pid: {'username': p['username'], 'score': p['score']} 
                           for pid, p in games[room].players.items()}
            }, room=room)

@socketio.on('disconnect')
def on_disconnect():
    for room in list(games.keys()):
        if request.sid in games[room].players:
            leave_room(room)
            del games[room].players[request.sid]
            emit('player_left', {'player': request.sid}, room=room)
            # If no players left in the room, delete the room
            if len(games[room].players) == 0:
                del games[room]

if __name__ == '__main__':
    # Remove eventlet dependency
    # import eventlet
    # eventlet.monkey_patch()
    
    # Use socketio.run directly
    socketio.run(app, host='127.0.0.1', port=3000, debug=True)