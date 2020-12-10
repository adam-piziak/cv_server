from flask import Flask, escape, request, jsonify
from flask.json import JSONEncoder
from flask_socketio import SocketIO, join_room, leave_room, send, emit
from flask_cors import CORS
import random
import numpy as np
import shortuuid
import math
import time
from arch import contract
from game import Game
from player import Player

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
socketio.run(app)
CORS(app)

games = {}

def create_game():
    global games
    game = Game(key, host)
    games[key] = game

    games[key].add_bot()
    games[key].add_bot()
    games[key].add_bot()    
    return (key, host)

@app.route('/create',methods=['POST'])
def create():
    global games
    game = Game()
    games[game.key] = game
    return jsonify(
        key = game.key,
        player = jsonify(player=games[game.key].players[0].serialize()).get_data(as_text=True)
    )

@app.route('/join',methods=['GET', 'POST'])
def validate_key():
    global games
    key = request.json['game_key']
    name = request.json['name']
    if request.json['game_key'] in games:
        player_key = games[key].add_player(name)
        return jsonify(
            player = jsonify(player=games[key].get_player(player_key).serialize()).get_data(as_text=True)
        )
    return jsonify(message="no")

@socketio.on('join_game')
def on_join(data):
    key = data['game_key']
    join_room(key)
    game_state = jsonify(game_state=games[key].serialize()).get_data(as_text=True)
    if len(games[key].players) > 3:
        games[key].deal_cards()
    emit("game_state", game_state, room=key)

@socketio.on('connect')
def on_connect():
    print("CONNECTED")
    emit("connect")

@socketio.on('start')
def on_start(data):
    print("START")
    key = data['game_key']
    games[key].check_for_bots()
    game_state = jsonify(game_state=games[key].serialize()).get_data(as_text=True)
    emit("game_state", game_state, room=key)    

@socketio.on('redeal')
def on_start(data):
    key = data['game_key']
    games[key].deal_cards()
    game_state = jsonify(game_state=games[key].serialize()).get_data(as_text=True)
    emit("game_state", game_state, room=key)    
    
@socketio.on('play_card')
def play_card(data):
    key = data['game_key']
    player_key = data['player_key']
    card_played = data['card_played']

    games[key].play_card(player_key, card_played)
    game_state = jsonify(game_state=games[key].serialize()).get_data(as_text=True)
    emit("game_state", game_state, room=key)

socketio.run(app, debug=True, host="0.0.0.0")

