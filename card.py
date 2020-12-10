class Card():
    SUIT_CLUBS = 0
    SUIT_DIAMONDS = 1
    SUIT_HEARTS = 2
    SUIT_SPADES = 3
    
    def __init__(self, card_num):
        self.suit = math.floor(card_num // 13)
        self.val = (card_num % 13) + 2


