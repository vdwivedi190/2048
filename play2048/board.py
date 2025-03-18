import numpy as np
import random
from random import Random

# Description: This file contains the Board2048 class which is used to represent the 2048 board.

DEFAULT_SIZE = 4

POS_SEED = random.randint(0, 2**32-1)
TILE_SEED = 20

PROB_TWO = 0.9

class Board2048:
    def __init__(self, size=DEFAULT_SIZE):
        self.size = size
        self.board = np.zeros((self.size,self.size),dtype=int)
        self.prev_board = np.copy(self.board)

        self.pos_rng = Random(POS_SEED)
        self.tile_rng = Random(TILE_SEED)


    def __str__(self):
        return '\n'.join([' '.join([str(cell) for cell in row]) for row in self.board])
    
    
    # Function to add a new tile at a random empty square 
    def add_tile(self):
        free_tiles = self.list_free_tiles()

        # Random.choices returns a list of length 1 by default
        pos = self.pos_rng.choices(free_tiles)[0]
        tile = self.tile_rng.choices([1,2], cum_weights=[PROB_TWO,1.0])[0]
        
        self.board[pos] = tile

        return pos, tile


    # Function to compute the list of free tiles on the board
    def list_free_tiles(self):
        return [ (i,j) 
            for i in range(self.size) 
            for j in range(self.size) 
            if self.board[i,j] == 0 ]
    

    # Takes a move ID and returns: 
    #  - start_pos: List of positions that correspond to the "lowest" tile
    #  - vdir: the "up" direction in which the tiles are scanned 
    def parse_move(self, move_id):
        match move_id:
            case 1:
                startpos = [np.array([0, i]) for i in range(self.size)]
                vdir = np.array([1, 0])
            case 2:
                startpos = [np.array([i,0]) for i in range(self.size)]
                vdir = np.array([0,1])
            case 3:
                startpos = [np.array([self.size-1, i]) for i in range(self.size)]
                vdir = np.array([-1, 0])
            case 4:
                startpos = [np.array([i,self.size-1]) for i in range(self.size)]
                vdir = np.array([0,-1])
            case _:
                raise ValueError("Invalid move!")
        return startpos, vdir


    # Function to implement a given move in self.board (saving the previous state in self.prev_board).  
    # Returns a list of moves (to be used by the graphics engine for animation)
    def move(self, move):
        pos_list, vdir = self.parse_move(move)
        tile_moves = []

        self.prev_board[:,:] = self.board[:,:]
        self.board[:,:] *= 0 
        new_pos = np.array([0,0])
                
        for start_pos in pos_list:         
            new_pos[:] = start_pos[:]
            prev_val = 0 
            
            for i in range(self.size):
                pos = start_pos + i * vdir
                val = self.prev_board[tuple(pos)]
                # Only need to do something if the square is nonempty
                if val != 0:
                    if prev_val != 0 and val == prev_val:
                        # Merge tiles 
                        self.board[tuple(new_pos - vdir)] += 1
                        prev_val = 0
                        tile_moves.append((tuple(pos), tuple(new_pos-vdir), True))
                        # tile_moves.append((tuple(pos), *self._calc_shift(pos, new_pos-vdir), True))
                    else:                 
                        # Move tile 
                        self.board[tuple(new_pos)] = val      

                        # Only add to the list of moves if the tile has moved
                        if (new_pos!=pos).any():
                            tile_moves.append((tuple(pos), tuple(new_pos), False))

                        prev_val = val
                        new_pos += vdir
        

        return tile_moves
    
    
    # Function to check if the game is over (no valid moves left)
    def gameover(self) -> bool:
        for i in range(self.size):
            for j in range(self.size):
                if self.board[i,j] == 0:
                    return False
                
            for j in range(self.size-1):                
                if self.board[i,j] == self.board[i,j+1]:
                    return False  
                if self.board[j,i] == self.board[j+1,i]:
                    return False

        return True
    

    def undo(self):
        self.board = np.copy(self.prev_board)
    
