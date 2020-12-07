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
    def __init__(self, key, num, is_host, name, is_bot):
        self.key = key
        self.is_host = is_host
        self.card_played = -1
        self.position = num
        self.tricks_won = 0
        self.name = name
        self.is_bot = True
        self.cards = []
        self.dummy = False

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

class RoundState():
    def __init__(self):
        self.cards_played = 0
        self.first_suit = -1

    def new_round(self, suit):
        self.car
        
class GameState():
    def __init__(self, key, host):
        self.key = key
        self.stage = STAGE_WAITING
        self.trump_suit = SUIT_CLUBS
        self.round_cards = []
        self.last_winner = 0
        self.turn_player = 0
        self.players = []
        self.players.append(PlayerState(host, 0, True, "Host", False))

    def get_player(self, key):
        for p in self.players:
            if p.key == key:
                return p

    def play_card(self, pk, c):
        player = self.get_player(pk)
        if player.position != self.turn_player:
            return False
        
        card = Card(c)
        first_suit = None
        if len(self.round_cards) > 0:
            first_suit = Card(self.round_cards[0]).suit
        else:
            first_suit = card.suit

        if len(self.round_cards):
            self.round_cards.append(c)
            player.play_card(c)
        elif player.has_suit(first_suit) and card.suit != first_suit:
            return False
        elif card.suit == first_suit:
            self.round_cards.append(c)
            player.play_card(c)
        elif not player.has_suit(first_suit):
            self.round_cards.append(c)
            player.play_card(c)
        else:
            return False

        self.turn_player = (self.turn_player + 1) % 4


        self.determine_winner()
        self.check_for_bots()
        return True

    def check_for_bots(self):
        turn_player = self.players[self.turn_player]

        if turn_player.is_bot:
            if not self.round_cards:
                #
                game_state = jsonify(game_state=self.serialize()).get_data(as_text=True)
                emit("game_state", game_state, room=self.key)
                time.sleep(1)
                #
                self.play_card(turn_player.key, turn_player.cards[0])
                return

            for i, c in enumerate(turn_player.cards):
                card = Card(c)
                #
                game_state = jsonify(game_state=self.serialize()).get_data(as_text=True)
                emit("game_state", game_state, room=self.key)
                #
                result = self.play_card(turn_player.key, turn_player.cards[i])
                if result:
                    return

        else:
            #game_state = jsonify(self.serialize()).get_data(as_text=True)
            #emit("game_state", game_state, room=self.key)
            game_state = jsonify(game_state=self.serialize()).get_data(as_text=True)
            emit("game_state", game_state, room=self.key)
            time.sleep(1)

    def determine_winner(self):
        if len(self.round_cards) < 4:
            return

        #
        game_state = jsonify(game_state=self.serialize()).get_data(as_text=True)
        emit("game_state", game_state, room=self.key)
        time.sleep(1)
        #
        winning_idx = 0 # Winning player index
        highest_value = 0
        trump_played = False

        cards = list(map(lambda c: Card(c), self.round_cards))
        first_suit = cards[0].suit
        for i in range(4):
            if cards[i].suit != first_suit and cards[i].suit != self.trump_suit:
                continue
            if trump_played and cards[i].suit != self.trump_suit:
                continue

            if not trump_played and cards[i].suit == self.trump_suit:
                trumpPlayed = True
                highestVal = cards[i].val
                winning_idx = i

            if cards[i].val > highest_value:
                winning_idx = i
                highest_value = cards[i].val

        winning_player_pos = (self.players[self.last_winner].position + winning_idx) % 4
        for key, val in enumerate(self.players):
            self.players[key].remove_card()
            if val.position == winning_player_pos:
                self.last_winner = val.position
                self.turn_player = val.position
                self.round_cards = []
                self.players[key].give_point()
                if len(self.players[key].cards) == 0:
                    self.declare_winner(key)

    def declare_winner(self, player_key):
        emit("winner", player_key)

    def deal_cards(self):
        deck = list(range(52))
        random.shuffle(deck)

        i = 0
        for key, value in enumerate(self.players):
            value.set_cards(deck[i:(i+13)])
            i += 13

        pl = self.players
        n = np.array(pl[0].cards)
        e = np.array(pl[1].cards)
        s = np.array(pl[2].cards)
        w = np.array(pl[3].cards)        
        declarer, trump_suit, contract_number = contract(n,s,e,w)
        self.stage = STAGE_PLAYING     

    def add_bot(self):
        id = uuid()
        player = PlayerState(id, len(self.players), False, "BOTSKI " + str(len(self.players)), True)
        self.players.append(player)
        if len(self.players) > 3:
            self.deal_cards()
            self.stage = STAGE_PLAYING

    def add_player(self, name):
        id = uuid()
        player = PlayerState(id, len(self.players), False, name, False)
        self.players[player.position] = player
        
        if len(self.players) > 3:
            self.deal_cards()

        return new_player

    def serialize(self):
        return {
            'game_key': self.key,
            'game_stage': self.stage,
            'turn_player': self.turn_player,
            'round_cards': self.round_cards,
            'players': [p.serialize() for _, p in enumerate(self.players)],
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
    games[key].add_bot()
    games[key].add_bot()
    games[key].add_bot()
    return (key, host)

@app.route('/create',methods=['GET', 'POST'])
def hello():
    global games
    key, host = create_game()
    return jsonify(
        key = key,
        player = jsonify(player=games[key].players[0].serialize()).get_data(as_text=True)
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
