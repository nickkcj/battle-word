# 🎮 Wordle Multiplayer

Uma versão multiplayer **em tempo real** do clássico Wordle, onde os jogadores competem para adivinhar a mesma palavra dentro de um limite de tempo ⏱️

## ✨ Funcionalidades

* Jogo multiplayer em tempo real 🕹️
* Limite de tempo de **5 minutos** por partida
* Sistema de pontos baseado na quantidade de acertos ⚡
* Partidas organizadas por salas
* Feedback com cores para cada tentativa 🟩🟨⬜

## ⚙️ Como Configurar

1. Instale o **Python 3.7** ou superior
2. Instale os pacotes necessários:

   ```
   pip install -r requirements.txt
   ```
3. Inicie o servidor:

   ```
   python app.py
   ```
4. Abra o navegador e acesse: `http://localhost:5000`

## 🧠 Como Jogar

1. Digite seu nome de usuário e um código de sala
2. Compartilhe o código com seus amigos para jogarem juntos
3. Você terá **5 minutos** para adivinhar o máximo de palavras de 5 letras
4. Os pontos são calculados com base na quantidade de acertos
5. Letras verdes = letra e posição corretas 🟩
6. Letras amarelas = letra certa na posição errada 🟨
7. Letras cinzas = letra não está na palavra ⬜

## 📏 Regras do Jogo

* Cada partida dura **5 minutos**
* Tentativas ilimitadas
* Se ninguém acertar a palavra no tempo, o jogo termina 🚫

