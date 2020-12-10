from arch import contract

class Bot():
    ARCH1 = 0
    ARCH2 = 1
    
    def __init__(self, bot_type):
        self.bot_type = bot_type

        if self.bot_type == Bot.ARCH2:
            self.model = arch_2([113,1000,1000,1000,1000,1000,1000,52],[0,0,0,0,0,0,0,0])
            self.model.eval()

    def pick_card(self, , ):
        card = -1

        if self.type == Bot.ARCH2:
            
        
        return card

    
