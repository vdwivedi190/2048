from .board import Board2048, DEFAULT_SIZE
from .cli import CLI
from .gui import GUI 
from .player import AIPlayer

# The move is encoded in an integer, which takes values 
# - 1,2,3,4 for up, left, down, right
# - 0 for undo
# - -1 to quit
# 1: up, 2: left, 3: down, 4: right


class Game:
    def __init__(self, graphics:bool=False, size:int=DEFAULT_SIZE, ai:bool=False):
        if size < 2:
            raise ValueError("Board size must be at least 2")
        
        self.board = Board2048(size)
        self.num_moves = 0
        self.undo_flag = False  # Flag to check if undo is possible
        
        if ai:
            self.player = AIPlayer()
        else:
            self.player = None

        if graphics:
            # self.graphics = GUI(size)
            raise NotImplementedError("GUI not implemented yet!")
        else:
            self.graphics = CLI(size)


    def play(self):
        self.board.add_tile()
        self.board.add_tile()

        self.graphics.draw_board(self.board.board)

        while True:
            if self.player is None:
                move_id = self.graphics.get_move()
            else:
                move_id = self.player.next_move(self.board)

            if move_id == -1:
                self.graphics.quit_game()
                break
            elif move_id == 0:
                if self.undo_flag:
                    self.undo_flag = False
                    self.num_moves -= 1
                    self.board.undo()
                    self.graphics.draw_board(self.board.board)
                    self.graphics.display_score(self.num_moves)
                elif self.num_moves == 0:
                    self.graphics.display_error("NO MOVES TO UNDO!")
                else:
                    self.graphics.display_error("CAN UNDO ONLY A SINGLE STEP!")
                    
                continue

            tile_moves = self.board.move(move_id)  
            # self.graphics.scr.addstr(0, 0, f"tile_moves = {tile_moves}")
            # self.graphics.scr.addstr(7, 0, "After move\n"+str(self.board.board))
            
            if len(tile_moves) == 0:  # Nothing to move!
                self.graphics.invalid_move()                
                continue
            else: 
                self.graphics.make_move(self.board.prev_board, self.board.board, move_id, tile_moves)
                self.graphics.draw_board(self.board.board)
                self.num_moves += 1
                self.undo_flag = True
                self.graphics.display_score(self.num_moves)
            
                        
            pos, tile = self.board.add_tile()
            self.graphics.add_new_tile(self.board.board, pos, tile)

            if self.board.gameover():
                self.graphics.gameover()
                break
