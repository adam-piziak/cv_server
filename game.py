from flask import jsonify
import random
from arch import contract
import numpy as np
from shortuuid import uuid
from player import Player
from server import socketio

STAGE_WAITING = 10
STAGE_PLAYING = 11

class Game():
    def __init__(self):
        self.key = uuid()
        self.players = []
        self.declarer = -1
        self.lead = -1
        self.turn = -1
        self.round_cards = []        
        self.trump_suit = -1
        self.contract_number = -1
        self.stage = STAGE_WAITING

        self.players.append(Player(0, True, "Host", False))        

    def get_player(self, key):
        for p in self.players:
            if p.key == key:
                return p

    def play_card(self, pk, c):
        player = self.get_player(pk)
        if player.position != self.turn:
            return False
        
        card = Card(c)
        lead_suit = None
        if len(self.round_cards) > 0:
            lead_suit = Card(self.round_cards[0]).suit
        else:
            lead_suit = card.suit

        if len(self.round_cards) == 0:
            self.round_cards.append(c)
            player.play_card(c)
        elif player.has_suit(lead_suit) and card.suit != lead_suit:
            return False
        elif card.suit == lead_suit:
            self.round_cards.append(c)
            player.play_card(c)
        elif not player.has_suit(lead_suit):
            self.round_cards.append(c)
            player.play_card(c)
        else:
            return False

        if player.is_bot and not player.dummy: 
            time.sleep(0.7)
            
        if player.dummy and self.players[(self.turn + 2) % 4].is_bot:
            time.sleep(0.7)
            
        if len(self.round_cards) < 4:
            self.turn = (self.turn + 1) % 4

        self.emit_state()
        self.determine_winner()
        self.check_for_bots()
        return True

    def check_for_bots(self):
        player = self.players[self.turn]

        if player.is_bot:
            # Let human choose move if dummy bot
            if player.dummy and not self.players[(self.turn + 2) % 4].is_bot:
                return
            
            if not self.round_cards:
                self.play_card(player.key, player.cards[0])
                self.emit_state()
                return

            for i, c in enumerate(player.cards):
                card = Card(c)
                result = self.play_card(player.key, player.cards[i])
                if result:
                    self.emit_state()
                    return

    def emit_state(self):
        game_state = jsonify(game_state=self.serialize()).get_data(as_text=True)
        socketio.emit("game_state", game_state, room=self.key)

    def determine_winner(self):
        if len(self.round_cards) < 4:
            return

        self.turn = -1
        self.emit_state()
        time.sleep(2)

        cards = list(map(lambda c: Card(c), self.round_cards))   
        winning_player = 0 # Winning player index
        highest_value = 0
        trump_played = False
        lead = cards[0].suit
        
        for i in range(4):
            if not trump_played and cards[i].suit == self.trump_suit:
                trump_played = True
                highest_value = cards[i].val
                winning_player = i
                
            if cards[i].suit != lead and cards[i].suit != self.trump_suit:
                continue

            if trump_played and cards[i].suit != self.trump_suit:
                continue

            if cards[i].val > highest_value:
                winning_player = i
                highest_value = cards[i].val

        winner = (self.lead + winning_player) % 4
        self.players[winner].give_point()
        self.players[(winner + 2) % 4].give_point()        
        self.lead = winner
        self.turn = winner        
        self.round_cards = []        
        for i, val in enumerate(self.players):
            self.players[i].remove_card()
        self.emit_state()
        if len(self.players[0].cards) == 0:
            self.declare_winner(pos)

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

        for pos, val in enumerate(self.players):
            if pos == declarer:
                self.players[pos].set_declarer(True)
            else: 
                self.players[pos].set_declarer(False)

            if pos == ((declarer + 2) % 4):
                self.players[pos].set_dummy(True)
            else:
                self.players[pos].set_dummy(False)
        self.lead = declarer
        self.turn = declarer
        self.trump_suit = trump_suit.item()
        self.contract_number = contract_number
        self.stage = STAGE_PLAYING
        self.round_cards = []
        self.emit_state()

    def add_bot(self):
        id = uuid()
        player = PlayerState(id, len(self.players), False, "BOTSKI " + str(len(self.players)), True)
        self.players.append(player)
        if len(self.players) > 3:
            self.deal_cards()

    def add_player(self, name):
        player = Player(len(self.players), False, name, False)
        self.players.append(player)
        
        if len(self.players) > 3:
            self.deal_cards()

        return player.key

    def serialize(self):
        return {
            'key': self.key,
            'game_stage': self.stage,
            'contract_number': self.contract_number,
            'lead': self.lead,
            'turn': self.turn,            
            'trump_suit': self.trump_suit,
            'round_cards': self.round_cards,
            'declarer': self.declarer,
            'players': [p.serialize() for _, p in enumerate(self.players)],
        }
