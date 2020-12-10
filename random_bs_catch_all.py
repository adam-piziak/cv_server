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
    """declarerOneHot = makeOneHot(cardState, declarer, 1, dummy)
    defender1OneHot = makeOneHot(cardState, (declarer+1) % 4, 0, dummy)
    defender2OneHot = makeOneHot(cardState, (declarer-1) % 4, 0, dummy)"""
    tsuit = torch.zeros((5))
    tsuit[trump_suit] = 1
    inputs = [None,None,None,None]
    inputs[declarer] = torch.cat((tsuit,torch.zeros((108))))
    inputs[(declarer+1) % 4] = torch.cat((tsuit,torch.zeros((108))))
    inputs[(declarer-1) % 4] = torch.cat((tsuit,torch.zeros((108))))
    declarer_points = 0
    As = [None,None,None,None]
    game_state = GameState(trump_suit)
    activePlayer = lead
    total_cards = []
    for trickNumber in range(13):
        lead = activePlayer
        activeCards = []
        for cidx in range(4):
            # pick which network for this turn
            if activePlayer == dummy:
                networkNumber = (activePlayer + 2) % 4
            else:
                networkNumber = activePlayer
            inputs[networkNumber][5+cidx] = 1
            mask = filterValidMoves(activeCards,hands[activePlayer])
            inputs[networkNumber][-104:-52] = torch.tensor(mask)
            #Note, the card indices get flipped when sent to inputs!
            inputs_old = inputs
            # use one-hot encoded input matrix for the network
            cardPlayed = getCardToPlay(modes[networkNumber],nets, networkNumber, inputs, activeCards, hands, activePlayer, game_state.trump_suit,mask)
            As[networkNumber] = cardPlayed
            activeCards.append(cardPlayed)
            for inp in inputs:
                if inp is None:
                    continue
                #inp[idx for idx in -1*(np.array(activeCards)+1).tolist()] = 1
                for sad in activeCards:
                    inp[-1*(sad+1)] = 1
            if cardPlayed in total_cards:
                print(networkNumber)
            total_cards.append(cardPlayed)
            """print(cardPlayed,networkNumber,trickNumber)
            print(inputs[networkNumber][-52:])"""

            # remove the card played from the hand of the active player
            idx = np.argwhere(hands[activePlayer]==cardPlayed)
            hands[activePlayer] = np.delete(hands[activePlayer],idx)

            # update one hot matrices
            """for inp in inputs:
                if inp is None:
                    continue
                inp[cardPlayed*5:cardPlayed*5+5] = torch.tensor([0,0,0,0,1])"""
            #This updates active 
            inputs[networkNumber][-cardPlayed-1] = 1
            #This updates legal 
            inputs[networkNumber][-104+cardPlayed] = 0
            """print(activeCards)
            print(inputs[networkNumber][260:265],inputs[networkNumber][265:269],inputs[networkNumber][-104:-52],inputs[networkNumber][-52:])
            quit()"""
            # go to the next player
            activePlayer = (activePlayer + 1) % 4

            # pass the chosen cards into the trick function and get the winner
            cards = []
            for num in activeCards:
                cards.append(number_to_card(num))
        
        winner = (determine_winner(game_state,cards) + lead) % 4
        activePlayer = winner
        winner2 = (winner + 2) % 4

    offset = declarer_points - (contract_number + 6)
    if offset >= 0:
        if not test:
            """mems[declarer].update_reward((1+offset)/8)
            mems[(declarer+1)%4].update_reward((-1-offset)/8)
            mems[(declarer-1)%4].update_reward((-1-offset)/8)"""
            return 1
        else: 
            return 1 if declarer == 0 or declarer == 2 else 0
    else: 
        if not test:
            """mems[declarer].update_reward((-1+offset)/4)
            mems[(declarer+1)%4].update_reward((1-offset)/4)
            mems[(declarer-1)%4].update_reward((1-offset)/4)"""
            return 0
        else: 
            return 1 if declarer == 1 or declarer == 3 else 0 
