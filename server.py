from flask import Flask, escape, request, jsonify
from flask.json import JSONEncoder
from flask_socketio import SocketIO, join_room, leave_room, send, emit
from flask_cors import CORS
import random
import shortuuid
import math

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
socketio.run(app)
CORS(app)

SUIT_CLUBS = 0
SUIT_DIAMONDS = 1
SUIT_HEARTS = 2
SUIT_SPADES = 3

STAGE_WAITING = 10
STAGE_PLAYING = 11

class Card():
    def __init__(self, card_num):
        self.suit = math.floor(card_num / 13)
        self.val = card_num % 13

class PlayerState():
    def __init__(self, key, num, is_host, name):
        self.key = key
        self.is_host = is_host
        self.card_played = -1
        self.position = num
        self.tricks_won = 0
        self.name = name
        self.cards = []

    def set_cards(self, cards):
        self.cards = cards

    def remove_card(self):
        self.card_played = -1

    def has_suit(self, suit):
        for card in self.cards:
            if Card(card).suit == suit:
                return True
        return False

    def play_card(self, card):
        if card in self.cards:
            self.card_played = card
            self.cards.remove(int(card))

    def give_point(self):
        self.tricks_won += 1

    def serialize(self):
        return {
            'key': self.key,
            'position': self.position,
            'is_host': self.is_host,
            'card_played': self.card_played,
            'tricks_won': self.tricks_won,
            'name': self.name,
            'cards': self.cards
        }

def chunks(l, n):
    for i in range(0, n):
        yield l[i::n]

class GameState():
    def __init__(self, key, host):
        self.key = key
        self.stage = STAGE_WAITING
        self.players = {}
        self.trump_suit = SUIT_CLUBS
        self.round_cards = []
        self.last_winner = host
        self.turn_player = 0
        self.players[host] = PlayerState(host, 0, True, "HOST")

    def play_card(self, player_key, card):
        if self.players[player_key].position != self.turn_player:
            return

        if not self.round_cards:
            self.round_cards.append(card)
            self.players[player_key].play_card(card)
        elif Card(card).suit == self.trump_suit:
            self.round_cards.append(card)
            self.players[player_key].play_card(card)
        elif Card(card).suit == Card(self.round_cards[0]).suit:
            self.round_cards.append(card)
            self.players[player_key].play_card(card)
        elif not self.players[player_key].has_suit(Card(self.round_cards[0]).suit):
            self.round_cards.append(card)
            self.players[player_key].play_card(card)
        else:
            return

        self.turn_player = (self.turn_player + 1) % 4

        self.determine_winner()

    def determine_winner(self):
        if len(self.round_cards) < 4:
            return

        winning_idx = 0 # Winning player index
        highest_value = 0
        trump_played = False

        cards = list(map(lambda c: Card(c), self.round_cards))
        first_suit = cards[0].suit
        for i in range(4):
            if cards[i].suit != first_suit:
                continue
            if not trump_played and cards[i].suit == self.trump_suit:
                trumpPlayed = True
                highestVal = cards[i].val
                winning_idx = i

            if trump_played and cards[i].suit != self.trump_suit:
                continue

            if cards[i].val > highest_value:
                winning_idx = i
                highest_value = cards[i].val

        winning_player_pos = (self.players[self.last_winner].position + winning_idx) % 4
        for key, val in self.players.items():
            self.players[key].remove_card()
            if val.position == winning_player_pos:
                self.last_winner = key
                self.turn_player = val.position
                self.round_cards = []
                self.players[key].give_point()

    def deal_cards(self):
        deck = list(range(52))
        random.shuffle(deck)

        i = 0
        for key, value in self.players.items():
            value.set_cards(deck[i:(i+13)])
            i += 13


    def add_player(self, name):
        new_player = uuid()
        self.players[new_player] = PlayerState(new_player, len(self.players), False, name)
        if len(self.players) > 3:
            self.deal_cards()
            self.stage = STAGE_PLAYING
        return new_player

    def serialize(self):
        return {
            'game_key': self.key,
            'game_stage': self.stage,
            'turn_player': self.turn_player,
            'round_cards': self.round_cards,
            'players': [p.serialize() for _, p in self.players.items()],
        }

games = {}

def uuid():
    return shortuuid.uuid()

def gen_invite_code():
    return uuid()[0:6].lower()

def create_game():
    global games
    key = uuid()
    host = uuid()
    game = GameState(key, host)
    games[key] = game
    return (key, host)

@app.route('/create',methods=['GET', 'POST'])
def hello():
    global games
    key, host = create_game()
    return jsonify(
        key = key,
        player = jsonify(player=games[key].players[host].serialize()).get_data(as_text=True)
    )

@app.route('/join',methods=['GET', 'POST'])
def validate_key():
    global games
    key = request.json['game_key']
    name = request.json['name']
    if request.json['game_key'] in games:
        player_key = games[key].add_player(name)
        return jsonify(
            player = jsonify(player=games[key].players[player_key].serialize()).get_data(as_text=True)
        )
    return jsonify(message="no")

@socketio.on('join_game')
def on_join(data):
    print("START JOIN")
    key = data['game_key']
    join_room(key)
    game_state = jsonify(game_state=games[key].serialize()).get_data(as_text=True)
    emit("game_state", game_state, room=key)
    print("JOIN FINISHED")

@socketio.on('connect')
def on_connect():
    print("CONNECTED")
    emit("connect")

@socketio.on('play_card')
def play_card(data):
    key = data['game_key']
    player_key = data['player_key']
    card_played = data['card_played']

    games[key].play_card(player_key, card_played)
    game_state = jsonify(game_state=games[key].serialize()).get_data(as_text=True)
    emit("game_state", game_state, room=key)

socketio.run(app, debug=True, host="0.0.0.0")
