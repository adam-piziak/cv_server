import numpy as np

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
