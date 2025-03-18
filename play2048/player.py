import random 
from board import Board2048

# Class to represent the AI player
# At the moment it just makes random moves
class AIPlayer:
    def __init__(self):
        self.ind = 0 

    def next_move(self, board:Board2048):
        move = random.choice([1,2,3,4])
        return move