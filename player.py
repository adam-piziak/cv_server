from shortuuid import uuid

class Player():
    def __init__(self, position, is_host, name, is_bot):
        self.key = uuid()
        self.is_host = is_host
        self.card_played = -1
        self.position = position
        self.tricks_won = 0
        self.name = name
        self.is_bot = is_bot
        self.cards = []
        self.dummy = False
        self.declarer = False

    def set_cards(self, cards):
        self.cards = cards

    def set_dummy(self, val): 
        self.dummy = val

    def set_declarer(self, val): 
        self.declarer = val        
        
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
            'bot': self.is_bot,
            'position': self.position,
            'is_host': self.is_host,
            'card_played': self.card_played,
            'points': self.tricks_won,
            'name': self.name,
            'cards': self.cards,
            'declarer': self.declarer,
            'dummy': self.dummy
        }
