import torch 
import numpy as np
import torch.nn.functional as F 
import torch.nn as NN 
from enum import Enum
import matplotlib.pyplot as plt
import math

class arch_1(NN.Module):
    
    def __init__(self,cdepth,cdropout,mdepth,mdropout,depth,dropout):
        if not type(cdepth) == list or not type(cdropout) == list or not type(mdepth) == list or not type(mdropout) == list or not type(depth) == list or not type(dropout) == list:
            print("Ya heccing DINGUS you didn't pass lists as arguments!")
            return None 
        if cdepth[-1] + mdepth[-1] != depth[0]:
            print("Invalid architecture! Size of each sub-output must sum to common input!")
            return None
        super(arch_1,self).__init__()
        self.card_layers = NN.ModuleList()
        self.meta_layers = NN.ModuleList()
        self.layers = NN.ModuleList()
        for i in range(len(depth)-1):
            self.layers.append(NN.Linear(depth[i],depth[i+1]))
            self.layers.append(NN.LeakyReLU())
            if dropout[i] != 0:
                self.layers.append(NN.Dropout(dropout[i]))
        for i in range(len(cdepth)-1):
            self.card_layers.append(NN.Linear(cdepth[i],cdepth[i+1]))
            self.card_layers.append(NN.LeakyReLU())
            if cdropout[i] != 0:
                self.card_layers.append(NN.Dropout(cdropout[i]))
        for i in range(len(mdepth)-1):
            self.meta_layers.append(NN.Linear(mdepth[i],mdepth[i+1]))
            self.meta_layers.append(NN.LeakyReLU())
            if mdropout[i] != 0:
                self.meta_layers.append(NN.Dropout(mdropout[i]))

    def forward(self,c,m):
        for layer in self.card_layers:
            c = layer(c)
        for layer in self.meta_layers:
            m = layer(m)
        x = torch.cat((c,m),1)
        for layer in self.layers:
            x = layer(x)
        return x


class arch_2(NN.Module):
    
    def __init__(self,depth,dropout):
        if not type(depth) == list or not type(dropout) == list:
            print("Ya heccing DINGUS you didn't pass lists as arguments!")
            return None 
        super(arch_2,self).__init__()
        self.layers = NN.ModuleList()
        for i in range(len(depth)-1):
            self.layers.append(NN.Linear(depth[i],depth[i+1]))
            self.layers.append(NN.LeakyReLU())
            if dropout[i] != 0:
                self.layers.append(NN.Dropout(dropout[i]))

    def forward(self,c):
        #x = torch.cat((c,m),1)
        x = c
        for layer in self.layers:
            x = layer(x)
        return x


class arch_3(NN.Module):
    
    def __init__(self,bdepth,bdropout,mdepth,mdropout,depth,dropout):
        if not type(bdepth) == list or not type(bdropout) == list or not type(mdepth) == list or not type(mdropout) == list or not type(depth) == list or not type(dropout) == list:
            print("Ya heccing DINGUS you didn't pass lists as arguments!")
            return None 
        if bdepth[-1] + mdepth[-1] != depth[0]:
            print("Invalid architecture! Size of each sub-output must sum to common input!")
            return None
        super(arch_3,self).__init__()
        self.mutual_layers = NN.ModuleList()
        self.meta_layers = NN.ModuleList()
        self.layers = NN.ModuleList()
        for i in range(len(depth)-1):
            self.layers.append(NN.Linear(depth[i],depth[i+1]))
            self.layers.append(NN.LeakyReLU())
            if dropout[i] != 0:
                self.layers.append(NN.Dropout(dropout[i]))
        for i in range(len(bdepth)-1):
            self.mutual_layers.append(NN.Linear(bdepth[i],bdepth[i+1]))
            self.mutual_layers.append(NN.LeakyReLU())
            if bdropout[i] != 0:
                self.mutual_layers.append(NN.Dropout(bdropout[i]))
        for i in range(len(mdepth)-1):
            self.meta_layers.append(NN.Linear(mdepth[i],mdepth[i+1]))
            self.meta_layers.append(NN.LeakyReLU())
            if mdropout[i] != 0:
                self.meta_layers.append(NN.Dropout(mdropout[i]))

    def forward(self,c,m):
        M = torch.cat((c,m),1)
        for layer in self.mutual_layers:
            M = layer(M)
        for layer in self.meta_layers:
            m = layer(m)
        x = torch.cat((M,m),1)
        for layer in self.layers:
            x = layer(x)
        return x


class Memory(object):

    def __init__(self,state_size,capacity):
        self.memory = torch.zeros((0,state_size*2+2)).cuda()
        self.cap = capacity
    def store(self,state,action,next_state,reward):
        row = torch.cat((state,torch.tensor([action],device="cuda"),torch.tensor([reward],device="cuda"),next_state))
        self.memory = torch.cat((self.memory,row.unsqueeze(0)),0)
        if self.memory.shape[0] > self.cap:
            self.memory = self.memory[-self.cap:,:]
    def update_reward(self,i,n=13):
        self.memory[-n:,-1] += i
    def batch(self,batch_size):
        idx = torch.randperm(self.memory.shape[0])
        return(self.memory[idx,:])
    def size(self):
        return(self.memory.shape[0])


def contract(n,s,e,w):
    # points for face cards
    n_points = np.sum(np.where(np.mod(n,13)-8 >=0,np.mod(n,13)-8,0))  
    s_points = np.sum(np.where(np.mod(s,13)-8 >=0,np.mod(s,13)-8,0))
    e_points = np.sum(np.where(np.mod(e,13)-8 >=0,np.mod(e,13)-8,0)) 
    w_points = np.sum(np.where(np.mod(w,13)-8 >=0,np.mod(w,13)-8,0))
    t1_points = n_points + s_points
    t2_points = e_points + w_points

    # number of cards in each suit
    n_suits = np.array([np.sum((n<=12) * (n>=0)),np.sum((n<=25) * (n>=13)),np.sum((n<=38) * (n>=26)),np.sum((n<=51) * (n>=39))])
    s_suits = np.array([np.sum((s<=12) * (s>=0)),np.sum((s<=25) * (s>=13)),np.sum((s<=38) * (s>=26)),np.sum((s<=51) * (s>=39))])
    e_suits = np.array([np.sum((e<=12) * (e>=0)),np.sum((e<=25) * (e>=13)),np.sum((e<=38) * (e>=26)),np.sum((e<=51) * (e>=39))])
    w_suits = np.array([np.sum((w<=12) * (w>=0)),np.sum((w<=25) * (w>=13)),np.sum((w<=38) * (w>=26)),np.sum((w<=51) * (w>=39))])
    t1_suits = n_suits + s_suits
    t2_suits = e_suits + w_suits

    # points in each suit
    n_suit_points = np.array([np.sum(np.where(np.mod(n,13)-8>=0,np.mod(n,13)-8,0)*(n<=12)*(n>=0)),np.sum(np.where(np.mod(n,13)-8>=0,np.mod(n,13)-8,0)*(n<=25)*(n>=13)),np.sum(np.where(np.mod(n,13)-8>=0,np.mod(n,13)-8,0)*(n<=38)*(n>=26)),np.sum(np.where(np.mod(n,13)-8>=0,np.mod(n,13)-8,0)*(n<=51)*(n>=39))])
    s_suit_points = np.array([np.sum(np.where(np.mod(s,13)-8>=0,np.mod(s,13)-8,0)*(s<=12)*(s>=0)),np.sum(np.where(np.mod(s,13)-8>=0,np.mod(s,13)-8,0)*(s<=25)*(s>=13)),np.sum(np.where(np.mod(s,13)-8>=0,np.mod(s,13)-8,0)*(s<=38)*(s>=26)),np.sum(np.where(np.mod(s,13)-8>=0,np.mod(s,13)-8,0)*(s<=51)*(s>=39))])
    e_suit_points = np.array([np.sum(np.where(np.mod(e,13)-8>=0,np.mod(e,13)-8,0)*(e<=12)*(e>=0)),np.sum(np.where(np.mod(e,13)-8>=0,np.mod(e,13)-8,0)*(e<=25)*(e>=13)),np.sum(np.where(np.mod(e,13)-8>=0,np.mod(e,13)-8,0)*(e<=38)*(e>=26)),np.sum(np.where(np.mod(e,13)-8>=0,np.mod(e,13)-8,0)*(e<=51)*(e>=39))])
    w_suit_points = np.array([np.sum(np.where(np.mod(w,13)-8>=0,np.mod(w,13)-8,0)*(w<=12)*(w>=0)),np.sum(np.where(np.mod(w,13)-8>=0,np.mod(w,13)-8,0)*(w<=25)*(w>=13)),np.sum(np.where(np.mod(w,13)-8>=0,np.mod(w,13)-8,0)*(w<=38)*(w>=26)),np.sum(np.where(np.mod(w,13)-8>=0,np.mod(w,13)-8,0)*(w<=51)*(w>=39))])
    t1_suit_points = n_suit_points + s_suit_points
    t2_suit_points = e_suit_points + w_suit_points

    # best suit calculation
    t1bs = np.argmax(t1_suits + t1_suit_points/100) #using suit points as tiebreaker
    t2bs = np.argmax(t2_suits + t2_suit_points/100)

    # singletons and voids
    n_singletons = np.sum(np.where(n_suits<=1,1,0)) 
    s_singletons = np.sum(np.where(s_suits<=1,1,0))
    e_singletons = np.sum(np.where(e_suits<=1,1,0)) 
    w_singletons = np.sum(np.where(w_suits<=1,1,0))
    t1_singletons = n_singletons + s_singletons
    t2_singletons = e_singletons + w_singletons

    # score for each player
    n_score = (n_points/40) + ((np.max(n_suits)-4)/20) + n_singletons/20
    s_score = (s_points/40) + ((np.max(s_suits)-4)/20) + s_singletons/20
    e_score = (e_points/40) + ((np.max(e_suits)-4)/20) + e_singletons/20
    w_score = (w_points/40) + ((np.max(w_suits-4))/20) + w_singletons/20
    t1_score = n_score + s_score 
    t2_score = e_score + w_score

    # 0 = north, 1 = east, 2 = south, 3 = west
    declarer = -1

    # 0 = clubs, 1 = diamonds, 2 = hearts, 3 = spades, 4 = no trump
    trump_suit = -1

    # can be between 1 and 6
    contract_number = -1

    # no one has enough points to bid
    if np.max(np.array([n_score,s_score,e_score,w_score])) < 0.30:
      return -1, -1, -1
    
    diff = np.abs(t1_score - t2_score)
    if t1_score>t2_score:
      # pick trump suit
      if t1_points >=28 and np.max(t1_suits) <=7:
        trump_suit = 4 # no trump
      else:
        trump_suit = t1bs
      # pick declarer
      if n_score > s_score:
        declarer = 0
      elif n_score < s_score:
        declarer = 2
      else:
        if n_suits[t2bs] > s_suits[t2bs]:
          declarer = 0
        else:
          declarer = 2
    else:
      # pick trump suit
      if t2_points >=28 and np.max(t2_suits) <=7:
        trump_suit = 4 # no trump
      else:
        trump_suit = t2bs
      # pick declarer
      if e_score > w_score:
        declarer = 1
      elif e_score < w_score:
        declarer = 3
      else: # tied in points, so pick the one with more in the best suit
        if e_suits[t2bs] > w_suits[t2bs]:
          declarer = 1
        else:
          declarer = 3
      
    # pick contract number
    if diff < 0.051:
      contract_number = 1
    elif diff < 0.21:
      contract_number = 2
    elif diff < 0.36:
      contract_number = 3
    elif diff < 0.61:
      contract_number = 4
    elif diff < 0.99:
      contract_number = 5
    else:
      contract_number = 6
    return declarer, trump_suit, contract_number


def deal():
    x = np.arange(0,52,1)
    np.random.shuffle(x)
    return(x[0:13],x[13:26],x[26:39],x[39:52])

suits = ["clubs","diamonds","hearts","spades"]
numbers = np.arange(2,15,1)
card_map = []
for i in range(4):
    for j in range(13):
        if j <= 8:
            cn = str(numbers[j])
        elif j == 9:
            cn = "Jack"
        elif j == 10: 
            cn = "Queen"
        elif j == 11:
            cn = "King"
        elif j == 12:
            cn = "Ace"
        card_map.append(cn+" of "+suits[i])


# cardState is the label encoded length-52 array, player is the current player (0-3), dummy is the dummy player's number (0-3)
def makeOneHot(cardState, player, isDeclarer, dummy):
  oneHot = torch.zeros([52,5])
  for i in range(0,52):
    cardOwner = cardState[i]
    if cardOwner == player:
      oneHot[i,0] = 1 #own hand
    elif cardOwner == dummy:
      if isDeclarer:
        oneHot[i,1] = 1 #friendly dummy
      else:
        oneHot[i,2] = 1 #opponent dummy
    else:
      oneHot[i,3] = 1 #hidden
  return torch.flatten(oneHot)


# cardsPlayed is a list of cards represented as 0-51
# returns a modified q_values vector that has 0s for invalid moves
def filterValidMoves(q_values,cardsPlayed,cardsInHand):
    if len(cardsPlayed) == 0:
        mask = np.zeros_like(q_values)
        mask[cardsInHand] = 1
        return np.multiply(q_values,mask)
    leadSuit = math.floor(cardsPlayed[0]//13)
    clubs, diamonds, hearts, spades = cardsBySuit(cardsInHand)
    cardsSuits = [clubs, diamonds, hearts, spades]

    if len(cardsSuits[leadSuit]) == 0 or len(cardsPlayed) == 0:
    # if there are no cards played (you are the lead) or you don't have any cards of the lead suit, keep all cards in hand
    # make a vector with ones at the indices in the lead suit and zeros otherwise
        mask = np.zeros_like(q_values)
        mask[cardsInHand] = 1
    else:
    # keep only cards in the lead suit
        mask = np.zeros_like(q_values)
        mask[cardsSuits[leadSuit]] = 1
    return np.multiply(q_values,mask)


def cardsBySuit(cards):
    clubs = np.where(cards < 13)
    diamonds = np.where((cards >= 13) & (cards < 27))
    hearts = np.where((cards >= 27) & (cards < 39))
    spades = np.where((cards >= 39) & (cards < 52))
    return cards[clubs],cards[diamonds], cards[hearts], cards[spades]


class Suit(Enum):
    CLUB = 0
    DIAMOND = 1
    HEART = 2
    SPADE = 3

class Card():
    def __init__(self, suit, value):
        self.suit = suit
        self.value = value

class GameState():
    def __init__(self, suit):
        self.trump_suit = suit

def create_deck():
  deck = []
  for suit in Suit:
    for val in range(13):
      deck.append(Card(suit, val + 1))
  return deck

def determine_winner(game_state, cards): #Check this ya dinguses somethin aint right 
    winning_player = 0 # Winning player index
    highest_value = 0
    trump_played = False
    lead = cards[0].suit
    highest_value = 0
    for i in range(4):
        if not trump_played and cards[i].suit == game_state.trump_suit:
            trump_played = True
            highest_value = cards[i].value
            winning_player = i
        
        if cards[i].suit != lead and cards[i].suit != game_state.trump_suit:
            continue

        if trump_played and cards[i].suit != game_state.trump_suit:
            continue

        if cards[i].value > highest_value:
            winning_player = i
            highest_value = cards[i].value

    return winning_player


def number_to_card(num):
    return Card(num//13,num%13+2)


def play_round(nets,mems,test,modes):  
    # Game flow: This block represents one episode
    #nets = [N,E,S,W]
    #mems = [Nm,Em,Sm,Wm]
    # assuming we have functions that determine the contract and who wins the trick


    # getting the contract
    declarer, trump_suit, contract_number = -1,-1,-1
    while declarer == -1:
        northHand, southHand, eastHand, westHand = deal()
        declarer, trump_suit, contract_number = contract(northHand,southHand,eastHand,westHand)
    dummy = (declarer + 2) % 4
    lead = (declarer + 1) % 4
    hands = [northHand, southHand, eastHand, westHand]

    # save the card state for the game. It will be one hot encoded for the neural networks
    # 0 = north's hand, 1 = east's hand, 2 = south's hand, 3 = west's hand, 4 = played
    cardState = torch.zeros(52)
    cardState[northHand] = 0
    cardState[southHand] = 2
    cardState[eastHand] = 1
    cardState[westHand] = 3

    # north is 0, east is 1, south is 2, west is 3 for purposes of play order

    # Card state (one-hot encoded)
    # [in your hand, in teammate's hand and visible (teammate dummy), in opponent's hand and visible (opponent dummy), hidden/unknown, played]
    # The three players each have their own separate card state matrices
    declarerOneHot = makeOneHot(cardState, declarer, 1, dummy)
    defender1OneHot = makeOneHot(cardState, (declarer+1) % 4, 0, dummy)
    defender2OneHot = makeOneHot(cardState, (declarer-1) % 4, 0, dummy)
    inputs = [None,None,None,None]
    inputs[declarer] = declarerOneHot
    inputs[(declarer+1) % 4] = defender1OneHot
    inputs[(declarer-1) % 4] = defender2OneHot
    declarer_points = 0
    As = [None,None,None,None]
    game_state = GameState(trump_suit)
    activePlayer = lead
    for trickNumber in range(13):
        lead = activePlayer
        activeCards = []
        inputs_old = inputs
        for cidx in range(4):
            # pick which network for this turn
            if activePlayer == dummy:
                networkNumber = (activePlayer + 2) % 4
            else:
                networkNumber = activePlayer
            
            # use one-hot encoded input matrix for the network
            cardPlayed = getCardToPlay(modes[activePlayer],nets, networkNumber, inputs, activeCards, hands, activePlayer, game_state.trump_suit)
            As[networkNumber] = cardPlayed
            activeCards.append(cardPlayed)

            # remove the card played from the hand of the active player
            idx = np.argwhere(hands[activePlayer]==cardPlayed)
            hands[activePlayer] = np.delete(hands[activePlayer],idx)

            # update one hot matrices
            for inp in inputs:
                if inp is None:
                    continue
                inp[cardPlayed*5:cardPlayed*5+5] = torch.tensor([0,0,0,0,1])

            # Create a memory instance for this trick for the active player


            # go to the next player
            activePlayer = (activePlayer + 1) % 4

            # pass the chosen cards into the trick function and get the winner
            cards = []
            for num in activeCards:
                cards.append(number_to_card(num))

        winner = (determine_winner(game_state,cards) + lead) % 4
        activePlayer = winner
        winner2 = (winner + 2) % 4
        if winner == declarer or winner2 == declarer:
            declarer_points += 1
            if not test:
                mems[declarer].store(inputs_old[declarer].cuda(),As[declarer],inputs[declarer].cuda(),1)
                mems[(declarer+1)%4].store(inputs_old[(declarer+1)%4].cuda(),As[(declarer+1)%4],inputs[(declarer+1)%4].cuda(),-1)
                mems[(declarer-1)%4].store(inputs_old[(declarer-1)%4].cuda(),As[(declarer-1)%4],inputs[(declarer-1)%4].cuda(),-1)
        else:
            if not test:
                mems[declarer].store(inputs_old[declarer].cuda(),As[declarer],inputs[declarer].cuda(),-1)
                mems[(declarer+1)%4].store(inputs_old[(declarer+1)%4].cuda(),As[(declarer+1)%4],inputs[(declarer+1)%4].cuda(),1)
                mems[(declarer-1)%4].store(inputs_old[(declarer-1)%4].cuda(),As[(declarer-1)%4],inputs[(declarer-1)%4].cuda(),1)
    
    offset = declarer_points - (contract_number + 6)
    if offset >= 0:
        if not test:
            mems[declarer].update_reward((1+offset)/4)
            mems[(declarer+1)%4].update_reward((-1-offset)/4)
            mems[(declarer-1)%4].update_reward((-1-offset)/4)
            return 1
        else: 
            return 1 if declarer == 0 or declarer == 2 else 0
    else: 
        if not test:
            mems[declarer].update_reward((-1+offset)/2)
            mems[(declarer+1)%4].update_reward((1-offset)/2)
            mems[(declarer-1)%4].update_reward((1-offset)/2)
            return 0
        else: 
            return 1 if declarer == 1 or declarer == 3 else 0 


def basicAIMove(handN, cardsPlayedN, trumpSuit):
    # convert to card class
    hand = []
    cardsPlayed = []
    for card in handN:
        hand.append(number_to_card(card))
    for card in cardsPlayedN:
        cardsPlayed.append(number_to_card(card))
    
    if len(cardsPlayed) == 0:
        # going first
        # play lowest value card in hand that is not a trump
        handNoTrumps = []
        for card in hand:
            if card.suit != trumpSuit:
                handNoTrumps.append(card)
        if len(handNoTrumps) == 0:
            return card_to_number(getLowest(hand))
        return card_to_number(getLowest(handNoTrumps))
    
    # when not going first, figure out valid moves
    leadSuit = cardsPlayed[0].suit
    valid = []
    trumps = []
    hasLeadSuit = 0
    for card in hand:
        if card.suit == leadSuit:
            valid.append(card)
            hasLeadSuit = 1
        if card.suit == trumpSuit: # getting trump cards
            trumps.append(card)
    
    # no card of lead suit, so all cards are valid
    if len(valid) == 0:
        valid = hand
        validNotTrumps = []
        for card in valid:
            if card.suit != trumpSuit:
                validNotTrumps.append(card)
 
    if len(cardsPlayed) == 1:
        # going second
        if hasLeadSuit: # play lowest card since you're second
            return card_to_number(getLowest(valid))
        else: # no lead suit, play lowest trump if you have it, else lowest value other card
            if len(trumps) > 0:
                return card_to_number(getLowest(trumps))
            else:
                return card_to_number(getLowest(valid))
    
    if len(cardsPlayed) == 2:
        # going third
        # if you have cards of the lead suit, play the highest since you're third
        # but if your highest can't beat the highest already played, play your lowest
        # if the lead suit is not trump, you have trumps and there are no trumps played, play the lowest trump that beats the other trumps
        # if you have no lead suit or trumps, play lowest value card
        if hasLeadSuit or leadSuit == trumpSuit:
            valueToBeat = cardsPlayed[0].value
            if cardsPlayed[1].suit == leadSuit and cardsPlayed[1].value > cardsPlayed[0].value:
                valueToBeat = cardsPlayed[1].value
            highest = getHighest(valid)
            if highest.value > valueToBeat:
                return card_to_number(highest)
            else:
                return card_to_number(getLowest(valid))
        else: # you have no lead suit cards and lead suit is not trumps
            if len(trumps) > 0:
                if cardsPlayed[1].suit == trumpSuit: # player 2 played a trump
                    if canBeat(cardsPlayed[1].value,trumps):
                        return card_to_number(getBest(cardsPlayed[1].value,trumps))
                    else:
                        if len(validNotTrumps) > 0:
                            return card_to_number(getLowest(validNotTrumps)) # can't beat player 2's trump, so play lowest non trump
                        else:
                            return card_to_number(getLowest(valid))
                else: # no trumps on the table
                    return card_to_number(getLowest(trumps))
            else: # you have no trumps
                return card_to_number(getLowest(valid))
    
    # going fourth
    # if you have cards of the lead suit, play best to win the trick
    # if you have no cards of the lead suit, play the best trump to win the trick
    # if you have no trumps, play the lowest value card
    if hasLeadSuit or leadSuit == trumpSuit:
        valueToBeat = cardsPlayed[0].value
        if cardsPlayed[1].suit == leadSuit and cardsPlayed[1].value > cardsPlayed[0].value:
            valueToBeat = cardsPlayed[1].value
        if cardsPlayed[2].suit == leadSuit and cardsPlayed[2].value > valueToBeat:
            valueToBeat = cardsPlayed[2].value
        return card_to_number(getBest(valueToBeat,valid))
    
    # you haev no lead suit cards and lead suit is not trumps
    if len(trumps) > 0:
        # see if player 2 or 3 played a trump
        valueToBeat = -1
        if cardsPlayed[1].suit == trumpSuit:
            valueToBeat = cardsPlayed[1].value
        if cardsPlayed[2].suit == trumpSuit:
            if cardsPlayed[2].value > valueToBeat:
                valueToBeat = cardsPlayed[2].value
        if valueToBeat == -1:
            return card_to_number(getLowest(trumps)) # play lowest trump because there are no trumps played
        if canBeat(valueToBeat,trumps):
            return card_to_number(getBest(valueToBeat,trumps))
        else: # can't beat the trumps played, so play lowest non trump
            if len(validNotTrumps) > 0:
                return card_to_number(getLowest(validNotTrumps))
            return card_to_number(getLowest(valid))
    
    # you have no lead suit cards and no trumps (sad)
    return card_to_number(getLowest(valid))


def getLowest(cards):
    lowest = cards[0]
    for card in cards:
        if card.value < lowest.value:
            lowest = card
    return lowest

def getHighest(cards):
    highest = cards[0]
    for card in cards:
        if card.value > highest.value:
            highest = card
    return highest

def canBeat(valueToBeat,cards):
    for card in cards:
        if card.value > valueToBeat:
            return True
    return False

# if you have cards that are higher than valueToBeat, play the lowest one that wins
# if you have no cards that are higher than valueToBeat, play the lowest card
def getBest(valueToBeat, cards):
    play = getLowest(cards)
    higher = []
    for card in cards:
        if card.value > valueToBeat:
            higher.append(card)
    if len(higher) == 0:
        return play
    return getLowest(higher)

def card_to_number(card):
    return card.suit * 13 + card.value-2

# modes: 0 = network, 1 = basicAI, 2 = UI, 3 = random
def getCardToPlay(mode, nets, networkNumber, inputs, activeCards, hands, activePlayer, trumpSuit):
    
    if mode == 0:
        # use one-hot encoded input matrix for the network
        q_values = nets[networkNumber](inputs[networkNumber].cuda())
 
        # filter out all invalid cards
        filteredResults = filterValidMoves(q_values.detach().cpu().numpy(),activeCards,hands[activePlayer])
        # pick the card with the highest Q value
        cardPlayed = np.argmax(filteredResults)
        return cardPlayed
    
    if mode == 1:
        return basicAIMove(hands[activePlayer],activeCards,trumpSuit)
 
    if mode == 3:
        return randomMove(hands[activePlayer],activeCards)

def randomMove(hand, activeCards):
    valid = []
    if len(activeCards) == 0:
        valid = hand
    else:
        leadSuit = activeCards[0]//13
        for card in hand:
            if card//13 == leadSuit:
                valid.append(card)
        if len(valid) == 0:
            valid = hand
    index = np.random.randint(0,len(valid))
    return valid[index]


N = arch_2([260,500,500,500,52],[0,0,0,0,0]).cuda()
Nt = arch_2([260,500,500,500,52],[0,0,0,0,0]).cuda()
S = arch_2([260,500,500,500,52],[0,0,0,0,0]).cuda() 
St = arch_2([260,500,500,500,52],[0,0,0,0,0]).cuda() 
E = arch_2([260,500,500,500,52],[0,0,0,0,0]).cuda() 
Et = arch_2([260,500,500,500,52],[0,0,0,0,0]).cuda() 
W = arch_2([260,500,500,500,52],[0,0,0,0,0]).cuda() 
Wt = arch_2([260,500,500,500,52],[0,0,0,0,0]).cuda() 
Nt.eval()
St.eval()
Et.eval()
Wt.eval()

Nt.load_state_dict(N.state_dict())
St.load_state_dict(S.state_dict())
Et.load_state_dict(E.state_dict())
Wt.load_state_dict(W.state_dict())

Nm = Memory(260,10000)
Sm = Memory(260,10000)
Em = Memory(260,10000)
Wm = Memory(260,10000)

Noptim = torch.optim.RMSprop(N.parameters(),lr=0.0001)
Soptim = torch.optim.RMSprop(S.parameters(),lr=0.0001)
Eoptim = torch.optim.RMSprop(E.parameters(),lr=0.0001)
Woptim = torch.optim.RMSprop(W.parameters(),lr=0.0001)

criterion = torch.nn.MSELoss()
batch_size = 32
gamma = 0.99
num_episodes = 10000
update = 10

def optimize_nets():
    if Nm.size() < batch_size or Sm.size() < batch_size or Em.size() < batch_size or Wm.size() < batch_size: 
        return 
    Nb = Nm.batch(batch_size)
    Sb = Sm.batch(batch_size)
    Eb = Em.batch(batch_size)
    Wb = Wm.batch(batch_size)
    #Xsav means state action values
    Nsav = N(Nb[:,0:260]).gather(1,Nb[:,260:261].long())
    Ssav = S(Sb[:,0:260]).gather(1,Sb[:,260:261].long())
    Esav = E(Eb[:,0:260]).gather(1,Eb[:,260:261].long())
    Wsav = W(Wb[:,0:260]).gather(1,Wb[:,260:261].long())
    #Xnsv means next state action values 
    Nnsv = Nt(Nb[:,-260:]).detach().max(1)[0].unsqueeze(1)
    Snsv = St(Sb[:,-260:]).detach().max(1)[0].unsqueeze(1)
    Ensv = Et(Eb[:,-260:]).detach().max(1)[0].unsqueeze(1)
    Wnsv = Wt(Wb[:,-260:]).detach().max(1)[0].unsqueeze(1)
    Ntarget = (Nnsv * gamma) + Nb[:,261:262]
    Starget = (Snsv * gamma) + Sb[:,261:262]
    Etarget = (Ensv * gamma) + Eb[:,261:262]
    Wtarget = (Wnsv * gamma) + Wb[:,261:262]
    Nloss = criterion(Nsav,Ntarget)
    Sloss = criterion(Ssav,Starget)
    Eloss = criterion(Esav,Etarget)
    Wloss = criterion(Wsav,Wtarget)
    Noptim.zero_grad()
    Soptim.zero_grad()
    Eoptim.zero_grad()
    Woptim.zero_grad()
    Nloss.backward()
    Sloss.backward()
    Eloss.backward()
    Wloss.backward()
    Noptim.step()
    Soptim.step()
    Eoptim.step()
    Woptim.step()

ma = []
perf = []
def train_nets():
    nets = [N,E,S,W]
    contracts_won = []
    mems = [Nm,Em,Sm,Wm]
    for n in range(num_episodes):
        w = play_round(nets,mems,0,[0,0,0,0])
        contracts_won.append(w)
        optimize_nets()
        if n % update == 0:
            Nt.load_state_dict(N.state_dict())
            St.load_state_dict(S.state_dict())
            Et.load_state_dict(E.state_dict())
            Wt.load_state_dict(W.state_dict())
        if n % 100 == 99:
            print(str(n+1),"Episodes completed!",str(sum(contracts_won[-100:])),"Contracts Won!",str(sum(contracts_won[-100:])/100),"Winrate")
            ma.append(sum(contracts_won[-100:])/100)
            perf.append(test_nets(N,S))
            print(str(perf[-1]),"Winrate against random agents")


def test_nets(N,S):
    nets = [N,None,S,None]
    wins = 0
    for _ in range(100):
        wins += play_round(nets,None,1,[0,3,0,3])
        #print(str(n),"Matches Played",str(wins),"Won",str(wins/(n+1)),"Winrate")
    return(wins/100)

train_nets()
torch.save(N.state_dict(),"baseline_blindfolded_bridge_nn_very_not_symmetric_reward_offsets.pth")
plt.plot(ma)
plt.xlabel("Episode (in hundreds)")
plt.ylabel("Average Declaring Team Winrate")
plt.title("lead = activePlayer")
plt.show()
plt.plot(perf)
plt.xlabel("Episode (in hundreds)")
plt.ylabel("Winrate against Random Agents")
plt.title("activePlayer = lead")
plt.show()
"""N.load_state_dict(torch.load("baseline_blindfolded_bridge_nn_very_not_symmetric_reward_offsets.pth"))
S.load_state_dict(torch.load("baseline_blindfolded_bridge_nn_very_not_symmetric_reward_offsets.pth"))
print(test_nets(N,S))"""
