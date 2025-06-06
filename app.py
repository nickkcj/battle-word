from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import random
import time
import os
import requests
from five_letter_words import words
from top1000_words import words_pt
import google.generativeai as genai
from dotenv import load_dotenv
import unicodedata

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')  # Use threading mode

# Game state
games = {}

# Basic word lists
WORDS = ['APPLE', 'BEACH', 'CLOUD', 'DREAM', 'EARTH', 'FLAME', 'GRASS', 'HEART', 
         'JUICE', 'KNIFE', 'LIGHT', 'MONEY', 'NIGHT', 'OCEAN', 'PEACE', 'QUEEN',
         'RADIO', 'SMILE', 'TIGER', 'UNITY', 'VOICE', 'WATER', 'YOUTH', 'ZEBRA']
PT_WORDS = ['AMIGO', 'BARCO', 'CHUVA', 'DENTE', 'FAROL', 'GRAMA', 'HOTEL', 
           'IDEIA', 'JANELA', 'LEITE', 'MUNDO', 'NOITE', 'PRATO', 'QUEDA',
           'ROUPA', 'SONHO', 'TEMPO', 'UNICO', 'VENTO', 'ZEBRA']

# Function to download word lists at startup if needed
def ensure_word_lists_exist():
    # URLs for comprehensive word lists
    english_url = "https://raw.githubusercontent.com/charlesreid1/five-letter-words/master/sgb-words.txt"
    portuguese_url = "https://www.ime.usp.br/~pf/dicios/br-utf8.txt"  # More reliable Portuguese dictionary
    
    # Get absolute file paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    english_path = os.path.join(base_dir, "english_words.txt")
    portuguese_path = os.path.join(base_dir, "portuguese_words.txt")
    
    # Download English words if needed
    if not os.path.exists(english_path) or os.path.getsize(english_path) < 10000:
        print("Downloading comprehensive English word list...")
        try:
            response = requests.get(english_url)
            if response.status_code == 200:
                with open(english_path, "w", encoding="utf-8") as f:
                    f.write(response.text)
                print(f"Downloaded {len(response.text.splitlines())} English words")
            else:
                print(f"Failed to download English words: HTTP {response.status_code}")
        except Exception as e:
            print(f"Error downloading English words: {e}")
    
    # Download Portuguese words if needed
    if not os.path.exists(portuguese_path) or os.path.getsize(portuguese_path) < 10000:
        print("Downloading comprehensive Portuguese word list...")
        try:
            response = requests.get(portuguese_url)
            if response.status_code == 200:
                # Extract only 5-letter words
                five_letter_words = []
                for word in response.text.splitlines():
                    word = word.strip().lower()
                    # Keep only pure alphabetic 5-letter words
                    if len(word) == 5 and all(c.isalpha() or c in 'áàãâéêíóôõúüç' for c in word):
                        # Normalize to remove accents
                        normalized_word = ''.join(c for c in unicodedata.normalize('NFD', word) 
                                               if unicodedata.category(c) != 'Mn')
                        five_letter_words.append(normalized_word.upper())
                
                # Write to file
                with open(portuguese_path, "w", encoding="utf-8") as f:
                    f.write('\n'.join(five_letter_words))
                print(f"Downloaded and filtered {len(five_letter_words)} Portuguese words")
                
                # If no words found, use a backup list
                if len(five_letter_words) < 100:
                    print("Not enough Portuguese words found, using backup list")
                    backup_words = generate_backup_portuguese_words()
                    with open(portuguese_path, "w", encoding="utf-8") as f:
                        f.write('\n'.join(backup_words))
                    print(f"Added {len(backup_words)} Portuguese words from backup")
            else:
                print(f"Failed to download Portuguese words: HTTP {response.status_code}")
                # Use backup immediately
                backup_words = generate_backup_portuguese_words()
                with open(portuguese_path, "w", encoding="utf-8") as f:
                    f.write('\n'.join(backup_words))
                print(f"Added {len(backup_words)} Portuguese words from backup")
        except Exception as e:
            print(f"Error downloading Portuguese words: {e}")
            # Use backup on exception
            backup_words = generate_backup_portuguese_words()
            with open(portuguese_path, "w", encoding="utf-8") as f:
                f.write('\n'.join(backup_words))
            print(f"Added {len(backup_words)} Portuguese words from backup due to error")

def generate_backup_portuguese_words():
    """Generate a reliable list of Portuguese 5-letter words"""
    return [word.upper() for word in [
        'SAGAZ', 'AMIGO', 'TERMO', 'NOBRE', 'SENSO', 'AFETO', 'ETNIA', 'ANEXO', 'TEMPO',
        'CASAL', 'DENGO', 'CAUSA', 'PODER', 'CORPO', 'COMUM', 'MENTE', 'SONHO', 'FESTA',
        'FORTE', 'MUNDO', 'PORTA', 'PRAIA', 'TERRA', 'FELIZ', 'CLARO', 'TARDE', 'NUNCA',
        'VERDE', 'AMIGO', 'BARCO', 'CHUVA', 'DENTE', 'FAROL', 'GRAMA', 'HOTEL', 'IDEIA',
        'JANELA', 'LEITE', 'MANHA', 'NOITE', 'PRATO', 'QUEDA', 'ROUPA', 'SONHO', 'TEMPO',
        'UNICO', 'VENTO', 'ZEBRA', 'BANDA', 'CONTA', 'DISCO', 'ESCOLA', 'FOLHA', 'GRUPO',
        'HOMEM', 'IDADE', 'JOVEM', 'LINHA', 'MORTE', 'NIVEL', 'ORDEM', 'PAPEL', 'QUASE',
        'REGRA', 'SAUDE', 'TRAÇO', 'UTERO', 'VALOR', 'XADREZ'
    ] if len(word) == 5]

# Debug function - add this to help troubleshoot
def debug_word_lists():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    english_path = os.path.join(base_dir, "english_words.txt")
    portuguese_path = os.path.join(base_dir, "portuguese_words.txt")
    
    print(f"Looking for word lists in: {base_dir}")
    print(f"English file exists: {os.path.exists(english_path)}")
    print(f"Portuguese file exists: {os.path.exists(portuguese_path)}")
    
    if os.path.exists(portuguese_path):
        with open(portuguese_path, "r", encoding="utf-8") as f:
            words = f.readlines()
        print(f"Portuguese file has {len(words)} words")
        if words:
            print(f"Sample Portuguese words: {words[:10]}")

# Function to load Portuguese words needs to be defined before it's used 
def load_portuguese_words_from_file():
    """Load Portuguese words from the text file into a list."""
    portuguese_words = []
    
    # Get absolute file path
    base_dir = os.path.dirname(os.path.abspath(__file__))
    portuguese_path = os.path.join(base_dir, "portuguese_words.txt")
    
    if os.path.exists(portuguese_path):
        try:
            with open(portuguese_path, "r", encoding="utf-8") as f:
                for line in f:
                    word = line.strip().upper()
                    if len(word) == 5:
                        portuguese_words.append(word)
            print(f"Loaded {len(portuguese_words)} Portuguese words from file")
        except Exception as e:
            print(f"Error loading Portuguese words from file: {e}")
    else:
        print(f"Portuguese words file not found at {portuguese_path}")
    
    return portuguese_words

# Load word lists efficiently
def load_word_lists():
    # Start with the hardcoded lists
    en_words = set(WORDS)
    pt_words = set(PT_WORDS)
    
    # Add words from five_letter_words and top1000_words modules
    en_words.update(words)
    pt_words.update(PORTUGUESE_WORD_LIST)
    
    # Extend with the downloaded word lists
    try:
        # English list
        base_dir = os.path.dirname(os.path.abspath(__file__))
        english_path = os.path.join(base_dir, "english_words.txt")
        portuguese_path = os.path.join(base_dir, "portuguese_words.txt")
        
        if os.path.exists(english_path):
            with open(english_path, "r", encoding="utf-8") as f:
                en_words.update(word.strip().upper() for word in f.readlines() if len(word.strip()) == 5)
        
        # Load additional Portuguese words if you have them
        if os.path.exists(portuguese_path):
            with open(portuguese_path, "r", encoding="utf-8") as f:
                pt_words.update(word.strip().upper() for word in f.readlines() if len(word.strip()) == 5)
                
        print(f"Loaded {len(en_words)} English words and {len(pt_words)} Portuguese words")
    except Exception as e:
        print(f"Error loading word lists: {e}")
    
    return en_words, pt_words

# Now execute these in the correct order:

# 1. First download/ensure the files exist
ensure_word_lists_exist()

# 2. Then load Portuguese words from file into global variable
PORTUGUESE_WORD_LIST = load_portuguese_words_from_file()

# 3. Only AFTER that, load the combined word lists
EN_VALID_WORDS, PT_VALID_WORDS = load_word_lists()

# Debug after everything is loaded
debug_word_lists()

def is_valid_word(word, language="english"):
    """Fast word validation using pre-loaded word sets with fallback"""
    word = word.strip().upper()
    
    # Basic validation
    if len(word) != 5 or not word.isalpha():
        return False
        
    # Check against our loaded word sets
    if language == "portuguese":
        return word in PT_VALID_WORDS
    else:
        return word in EN_VALID_WORDS

def get_gemini_word(language="english"):
    """Get a word from Gemini API with fallback to random word"""
    try:
        GOOGLE_API_KEY = os.getenv('GEMINI_API_KEY')
        if not GOOGLE_API_KEY:
            raise ValueError("No GEMINI_API_KEY found in environment variables")
            
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        if language == "portuguese":
            prompt = (
                "Dê-me uma palavra comum em português com exatamente 5 letras. "
                "Retorne apenas a palavra, sem nada mais. "
                "Não use acentos ou caracteres especiais."
            )
        else:  # Default to English
            prompt = (
                "Give me a single, common English word with exactly 5 letters. "
                "Just return the word, nothing else."
            )
        
        response = model.generate_content(prompt)
        word = response.text.strip().upper()
        
        # Validate the word (should be 5 letters, alphabetic)
        if len(word) == 5 and word.isalpha() and is_valid_word(word, language):
            return word
        else:
            # Fallback to a random word from the appropriate list
            if language == "portuguese":
                return random.choice(PT_WORDS)
            else:
                return random.choice(WORDS)
    except Exception as e:
        print(f"Error getting word from Gemini API: {e}")
        # Fallback to a random word
        if language == "portuguese":
            return random.choice(PT_WORDS)
        else:
            return random.choice(WORDS)

class Game:
    def __init__(self, language="english"):
        self.players = {}
        self.start_time = None
        self.game_duration = 300  # 5 minutes in seconds
        self.game_started = False
        self.language = language
        
    def add_player(self, player_id, username):
        self.players[player_id] = {
            'username': username,
            'guesses': [],
            'score': 0,
            'current_word': get_gemini_word(self.language)
        }
    
    def start_game(self):
        if self.game_started:
            return False
        
        self.game_started = True
        self.start_time = time.time()
        
        # Generate new words for all players
        for player_id in self.players:
            self.players[player_id]['current_word'] = get_gemini_word(self.language)
        
        return True
    
    def is_game_over(self):
        if not self.game_started:
            return False
        
        now = time.time()
        return (now - self.start_time) >= self.game_duration
    
    def remaining_time(self):
        if not self.game_started:
            return self.game_duration
        
        now = time.time()
        elapsed = now - self.start_time
        remaining = self.game_duration - elapsed
        
        return max(0, remaining)
    
    def make_guess(self, player_id, guess):
        if player_id not in self.players or not self.game_started:
            return False
        
        guess = guess.upper()
        if len(guess) != 5:
            return False
            
        # Check if the word is valid in the current language
        if not is_valid_word(guess, self.language):
            return "invalid_word"

        current_word = self.players[player_id]['current_word']
        
        # Count letter occurrences in the target word
        letter_counts = {}
        for letter in current_word:
            letter_counts[letter] = letter_counts.get(letter, 0) + 1
        
        # First pass: mark correct positions
        result = ['absent'] * 5
        for i, letter in enumerate(guess):
            if letter == current_word[i]:
                result[i] = 'correct'
                letter_counts[letter] = max(0, letter_counts.get(letter, 0) - 1)
        
        # Second pass: mark present letters (but only if we have remaining counts)
        for i, letter in enumerate(guess):
            if result[i] != 'correct' and letter in letter_counts and letter_counts[letter] > 0:
                result[i] = 'present'
                letter_counts[letter] -= 1

        self.players[player_id]['guesses'].append({
            'word': guess,
            'result': result
        })

        if guess == current_word:
            self.players[player_id]['score'] += 1
            self.players[player_id]['current_word'] = get_gemini_word(self.language)
            return True

        return False

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def on_join(data):
    room = data['room']
    username = data['username']
    language = data.get('language', 'english')  # Default to English if not specified
    
    if room not in games:
        games[room] = Game(language=language)
    elif len(games[room].players) == 0:
        games[room] = Game(language=language)
    
    join_room(room)
    games[room].add_player(request.sid, username)
    
    # Send initial game state to the new player
    emit('game_state', {
        'word_length': 5,
        'game_started': games[room].game_started,
        'language': games[room].language
    }, room=request.sid)
    
    # Broadcast updated player list to all players in the room
    emit('players_update', {
        'players': {pid: {'username': p['username'], 'score': p['score']} 
                  for pid, p in games[room].players.items()}
    }, room=room)

@socketio.on('disconnect')
def on_disconnect():
    for room, game in list(games.items()):
        if request.sid in game.players:
            leave_room(room)
            del game.players[request.sid]
            
            # If room is empty, remove it
            if not game.players:
                del games[room]
                continue
            
            # Broadcast updated player list
            emit('players_update', {
                'players': {pid: {'username': p['username'], 'score': p['score']} 
                          for pid, p in game.players.items()}
            }, room=room)

@socketio.on('start_game')
def on_start_game(data):
    room = data['room']
    if room in games:
        if games[room].start_game():
            emit('game_started', {'duration': games[room].game_duration}, room=room)
            
            # Start a background task to notify players of time remaining
            def send_time_updates():
                while room in games and not games[room].is_game_over():
                    socketio.sleep(1)
                    remaining = games[room].remaining_time()
                    socketio.emit('time_update', {'remaining': remaining}, room=room)
                    
                    if remaining <= 0:
                        socketio.emit('game_over', {
                            'players': {pid: {'username': p['username'], 'score': p['score']} 
                                      for pid, p in games[room].players.items()}
                        }, room=room)
                        break
            
            socketio.start_background_task(send_time_updates)

@socketio.on('guess')
def on_guess(data):
    room = data['room']
    guess = data['guess']
    
    if room in games:
        result = games[room].make_guess(request.sid, guess)
        
        # Handle invalid word case
        if result == "invalid_word":
            emit('guess_error', {
                'message': 'That word doesn\'t exist in this language!'
            }, room=request.sid)
            return
            
        if request.sid in games[room].players:
            last_guess = games[room].players[request.sid]['guesses'][-1]
            username = games[room].players[request.sid]['username']
            
            # Send result to the player who made the guess
            emit('guess_result', {
                'guess': guess,
                'result': last_guess['result'],
                'success': result == True,
                'new_word': games[room].players[request.sid]['current_word'] if result == True else None
            }, room=request.sid)
            
            # If correct guess, notify other players and update scores
            if result == True:
                # Notify other players
                emit('player_correct', {
                    'username': username
                }, room=room, include_self=False)  # Sends to everyone in room except sender
                
                # Broadcast updated scores to all players
                emit('scores_update', {
                    'players': {pid: {'username': p['username'], 'score': p['score']} 
                              for pid, p in games[room].players.items()}
                }, room=room)

@socketio.on('next_word')
def on_next_word(data):
    room = data['room']
    
    if room in games and request.sid in games[room].players:
        # Save the old word before changing it
        player = games[room].players[request.sid]
        old_word = player['current_word']
        
        # Generate a new word for the player
        player['current_word'] = get_gemini_word(games[room].language)
        
        # Show a message without revealing the new word
        emit('new_word', {
            'message': 'New word ready!'
        }, room=request.sid)

port = int(os.getenv("PORT", 5000))

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
