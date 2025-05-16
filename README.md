# Multiplayer Wordle

A real-time multiplayer version of the popular Wordle game where players compete to guess the same word within a time limit.

## Features

- Real-time multiplayer gameplay
- 5-minute time limit per game
- Point system based on how quickly you guess the word
- Room-based gameplay
- Live player list with scores
- Color-coded feedback for guesses

## Setup

1. Install Python 3.7 or higher
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Run the server:
   ```
   python app.py
   ```
4. Open your browser and navigate to `http://localhost:5000`

## How to Play

1. Enter your username and a room code
2. Share the room code with friends to play together
3. You have 5 minutes to guess the 5-letter word
4. Points are awarded based on how quickly you guess the word
5. Green letters indicate correct position
6. Yellow letters indicate correct letter, wrong position
7. Gray letters indicate letter not in the word

## Game Rules

- Each game lasts 5 minutes
- Players can make unlimited guesses
- Points are calculated based on time remaining
- The first player to guess the word correctly wins
- If no one guesses the word in time, the game ends 