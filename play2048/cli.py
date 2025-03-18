import curses 
from time import sleep
from numpy import sign
from .colors import COLORS

DEBUG_FLAG = False

# DICIONARY OF SYMBOLS FOR THE TILES
SYMBOLS = {i:str(2**i) for i in range(1, 16)}
SYMBOLS[0] = " "     # Empty tile 
SYMBOLS[-1] = "??"   # Wildcard tile

# SIZE CONSTANTS 
TILE_NROWS, TILE_NCOLS = 3, 9
BORDER_WIDTH = 1
TILE_HEIGHT = TILE_NROWS + BORDER_WIDTH
TILE_WIDTH = TILE_NCOLS + BORDER_WIDTH
TILE_VOFFSET = 1
TILE_HOFFSET = 2
TXT_WIDTH = 7

# MARGINS 
TOP_MARGIN = 5
BOTTOM_MARGIN = 5
SIDE_MARGIN = 10

# BOX CHARACTERS FOR DRAWING THE GRID
C_VERT, C_HORZ = '┃', '━'
C_TL, C_TR, C_BL, C_BR = '┏', '┓', '┗', '┛'
C_MID_U, C_MID_D, C_MID_L, C_MID_R, C_MID_C = '┳', '┻', '┣', '┫', '╋'

C_WIDE_T, C_WIDE_B, C_WIDE_L, C_WIDE_R = '▀', '▄', '▌', '▐'
C_WIDE_TL, C_WIDE_TR, C_WIDE_BL, C_WIDE_BR = '▛', '▜', '▙', '▟'
C_FULL = '█'

VSTEP = 1 
HSTEP = 1

# MOVES 
KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT = 'w', 's', 'a', 'd'
KEY_UNDO, KEY_QUIT = 'u', 'q'
MOVE_DICT = {KEY_UP:1, KEY_LEFT:2, KEY_DOWN:3, KEY_RIGHT:4, KEY_UNDO:0, KEY_QUIT:-1}

# COLORS 
ORIG_BKGCOLOR = COLORS.BKGD
GRIDLINES_COLOR = COLORS.BRIGHT_BLACK

TILE_TXTCOLOR, TILE_BKGCOLOR = COLORS.BRIGHT_BLACK, COLORS.BRIGHT_WHITE
NEW_TILE_TXTCOLOR, NEW_TILE_BKGCOLOR = COLORS.BRIGHT_WHITE, COLORS.BRIGHT_BLACK 
MERGED_TILE_TXTCOLOR, MERGED_TILE_BKGCOLOR = COLORS.BLACK, COLORS.BRIGHT_RED
MOV_TILE_TXTCOLOR, MOV_TILE_BKGCOLOR = COLORS.BLACK, COLORS.BRIGHT_CYAN
WILD_TILE_TXTCOLOR, WILD_TILE_BKGCOLOR = COLORS.BRIGHT_WHITE, COLORS.BRIGHT_BLACK

TITLE_TXTCOLOR, TITLE_BKGCOLOR = COLORS.BRIGHT_GREEN, ORIG_BKGCOLOR
SCORE_TXTCOLOR, SCORE_BKGCOLOR = COLORS.BRIGHT_CYAN, ORIG_BKGCOLOR
MSG_TXTCOLOR, MSG_BKGCOLOR = COLORS.BRIGHT_CYAN, ORIG_BKGCOLOR
ERR_TXTCOLOR, ERR_BKGCOLOR = COLORS.BRIGHT_RED, ORIG_BKGCOLOR


# STRINGS FOR DISPLAY
TITLE_STR = "🯉  🯲 🯰 🯴 🯸  🯉"
INSTR_STR = " [Press w/s/a/d for movement, q for exit]"
COPYRIGHT_STR = "© 2025 Vatsal Dwivedi. All rights reserved."

DELAYS = {'v':0.06, 'h':0.02, 'm':0.2}

class CLI:

    # CONSTRUCTOR AND DESTRUCTOR
    # =================================================================

    def __init__(self, size):

        """
            The game takes place inside a window, which is always centered in the terminal.
        """
        self.size = size

        # Initialize curses screen
        self.scr = self._init_scr()
        
        # Use the terminal window size to determine the size of the game window
        self.scr_height, self.scr_width = self.scr.getmaxyx()   
        self._comp_lengths()

        self._init_fonts()            
        
        # Create the subwindows sub.window and sub.game 
        try:
            self._create_windows()
        except ValueError as e:
            self.scr.addstr(0,0,str(e))
            # self.scr.getch() 
            return None 
        except:
            raise ValueError("Error creating window!")
        
        self._draw_banner()
        self._draw_grid()
        self.window.refresh()
    


    def __del__(self):
        if DEBUG_FLAG:
            sleep(10)
        self.scr.getch()
        curses.resetty()
        curses.endwin()



    # INITIALIZATION ROUNTINES
    # =================================================================
    def _init_scr(self):
        # Standard curses initialization
        scr = curses.initscr()
        # scr.clear()
        
        # Save the terminal state before making any changes 
        self.tty_state = curses.savetty()

        # Turn off key echoing and enable hide the cursor
        curses.noecho()
        curses.cbreak()
        curses.curs_set(False)

        # Enable color if available
        try:
            curses.start_color()

            # This allows the use of the default terminal background color
            curses.use_default_colors()
        except:
            pass

        return scr
    

    # Compute the sizes and positions of various windows 
    def _comp_lengths(self) -> None:
        """
            The width and height of the window are determined by the size of the game board.
            The top-left corner of the window is at (board_row, board_col) in the terminal.window
            as measured in the original terminal coordinates. 
        """
        
        # Width and Height of the game board. 
        # The width has one additional column on each side 
        self.board_width = self.size*(TILE_NCOLS+BORDER_WIDTH) + 3
        self.board_height = self.size*(TILE_HEIGHT) + 1

        # Width and Height of the window.         
        self.win_width = self.board_width + 2*SIDE_MARGIN
        self.win_height = self.board_height + TOP_MARGIN + BOTTOM_MARGIN

        # Top-left corner of the window in the terminal coordinates
        self.win_row = (self.scr_height - self.win_height) // 2
        self.win_col = (self.scr_width - self.win_width) // 2

        # Top-left corner of the game board in the window coordinates
        self.board_row = TOP_MARGIN
        self.board_col = SIDE_MARGIN

        # Center of the board in the window coordinates
        self.center_col = self.win_width // 2 

        # Row for title and message displays in the window coordinates
        self.title_row = 1
        self.score_row = 3
        self.msg_row = self.win_height - 4

        # Empty string of the same length as the window width
        self.empty_str = " " * (self.win_width-3)

    
    # Create the subwin and the board window inside the terminal
    def _create_windows(self):        
        if self.win_row < 0 or self.win_col < 0:
            raise ValueError("Terminal too small for the game. Press any key to abort!")
        
        try:
            # The created window is one column wider than self.win_width. This is to avoid the 
            # bug in curses.addstr() that throws an error when writing to the bottom-right cell
            self.window = self.scr.derwin(self.win_height, self.win_width+1, 
                                          self.win_row, self.win_col)
            self.board = self.window.derwin(self.board_height, self.board_width+1, 
                                            self.board_row, self.board_col)
        except:
            raise curses.error 
        
        self.window.border()
    

    def _init_fonts(self):                
        self.tile_attr = curses.A_BOLD
        self.new_tile_attr = self.tile_attr
        self.mov_tile_attr = self.tile_attr
        self.merged_tile_attr = self.tile_attr
        self.wild_tile_attr = self.tile_attr
        
        self.title_attr = curses.A_BOLD
        self.score_attr = curses.A_ITALIC | curses.A_BOLD        
        self.msg_attr = curses.A_NORMAL
        self.err_attr = curses.A_ITALIC | curses.A_BOLD
        self.grid_attr = curses.A_NORMAL
        
        if curses.has_colors():        
            # Bitwise OR with the color attribute bitstring
            curses.init_pair(1, GRIDLINES_COLOR, TILE_BKGCOLOR)
            self.grid_attr |= curses.color_pair(1)
            
            curses.init_pair(2, TILE_TXTCOLOR, TILE_BKGCOLOR)
            self.tile_attr |= curses.color_pair(2)
            
            curses.init_pair(3, NEW_TILE_TXTCOLOR, NEW_TILE_BKGCOLOR)            
            self.new_tile_attr |= curses.color_pair(3)

            curses.init_pair(4, MOV_TILE_TXTCOLOR, MOV_TILE_BKGCOLOR)            
            self.mov_tile_attr |= curses.color_pair(4)

            curses.init_pair(5, MERGED_TILE_TXTCOLOR, MERGED_TILE_BKGCOLOR)            
            self.merged_tile_attr |= curses.color_pair(5)

            curses.init_pair(6, WILD_TILE_TXTCOLOR, WILD_TILE_BKGCOLOR)            
            self.wild_tile_attr |= curses.color_pair(6)

            curses.init_pair(12, TITLE_TXTCOLOR, TITLE_BKGCOLOR)
            self.title_attr |= curses.color_pair(12)

            curses.init_pair(13, SCORE_TXTCOLOR, SCORE_BKGCOLOR)
            self.score_attr |= curses.color_pair(13)

            curses.init_pair(14, MSG_TXTCOLOR, MSG_BKGCOLOR)
            self.msg_attr |= curses.color_pair(14)
            
            curses.init_pair(15, ERR_TXTCOLOR, ERR_BKGCOLOR)
            self.err_attr |= curses.color_pair(15)


    # Function to add the title and other standard stuff
    def _draw_banner(self):        
        # Print the instructions in the space for the score
        self.window.addstr(self.title_row, SIDE_MARGIN, TITLE_STR.center(self.board_width), self.title_attr)
        self.window.addstr(self.score_row, SIDE_MARGIN, INSTR_STR.center(self.board_width), self.score_attr)
        self.window.addstr(self.win_height-2, SIDE_MARGIN, COPYRIGHT_STR.center(self.board_width), curses.A_NORMAL)

 
    # Function to draw a grid for the game
    def _draw_grid(self):
        str_top = ' ' + C_TL + (C_HORZ*TILE_NCOLS + C_MID_U)*(self.size-1) + C_HORZ*TILE_NCOLS + C_TR + ' '
        str_mid = ' ' + C_MID_L + (C_HORZ*TILE_NCOLS + C_MID_C)*(self.size-1) + C_HORZ*TILE_NCOLS + C_MID_R + ' '
        str_bottom = ' ' + C_BL + (C_HORZ*TILE_NCOLS + C_MID_D)*(self.size-1) + C_HORZ*TILE_NCOLS + C_BR + ' '
        str_space = ' ' + C_VERT + (' '*TILE_NCOLS + C_VERT)*(self.size) + ' '

        self.board.addstr(0, 0, str_top, self.grid_attr)
        for i in range(self.size):
            tile_row = i * (TILE_HEIGHT) 
            for j in range(TILE_NROWS):
                self.board.addstr(tile_row + j + 1, 0, str_space, self.grid_attr)
            self.board.addstr(tile_row + TILE_NROWS + 1, 0, str_mid, self.grid_attr)
        self.board.addstr(self.board_height-1, 0, str_bottom, self.grid_attr)
    



    # TILE ROUNTINES
    # =================================================================

    def _pos_from_ind(self, ind:tuple) -> tuple:
        row = ind[0] * (TILE_HEIGHT) + BORDER_WIDTH - 1
        col = ind[1] * (TILE_NCOLS+BORDER_WIDTH) + BORDER_WIDTH
        return row, col
    

    # Function to compute the corner characters for a tile at index ind = (i,j)
    # The tiles at the edges/corners must have different corner characters
    def _comp_corners(self, ind:tuple) -> tuple:
        r,c = ind
        tl = tr = bl = br = C_MID_C 

        # Deal with corner tiles followed by edge tiles
        if r == 0 and c == 0:  # Top-left corner
            tl, tr, bl = C_TL, C_MID_U, C_MID_L
        elif r == 0 and c == self.size - 1:  # Top-right corner
            tl, tr, br = C_MID_U, C_TR, C_MID_R
        elif r == self.size - 1 and c == 0:  # Bottom-left corner
            tl, bl, br = C_MID_L, C_BL, C_MID_D
        elif r == self.size - 1 and c == self.size - 1:  # Bottom-right corner
            tr, bl, br = C_MID_R, C_MID_D, C_BR
        elif r == 0:  # Top edge
            tl = tr = C_MID_U
        elif r == self.size - 1:  # Bottom edge
            bl = br = C_MID_D   
        elif c == 0:  # Left edge
            tl = bl = C_MID_L
        elif c == self.size - 1:  # Right edge
            tr = br = C_MID_R

        return tl, tr, bl, br
    

    # Function to draw the gridlines around a tile at position pos (in the board coordinates)
    # The corners of the tile are specified by the tuple corners = (tl, tr, bl, br)
    # This can be used to also draw the gridlines around a shifted tile
    def _draw_tile_border(self, pos:tuple, attr:int, corners:tuple = (C_TL, C_TR, C_BL, C_BR)) -> None:        
        row, col = pos

        if len(corners) != 4:
            raise ValueError("Invalid corner specification!")
        if row < 0 or row > self.board_height - TILE_NROWS - 2\
              or col < 0 or col > self.board_width - TILE_NCOLS - 2:
            raise ValueError(f"Cannot draw a tile with top-left corner at {row, col}!")

        tl, tr, bl, br = corners        

        str_top = tl + C_HORZ*TILE_NCOLS + tr
        str_space = C_VERT + ' '*TILE_NCOLS + C_VERT
        str_bottom = bl + C_HORZ*TILE_NCOLS + br

        self.board.addstr(row, col, str_top, attr)
        for i in range(TILE_NROWS):
            self.board.addstr(row + i + 1, col, str_space, attr)
        self.board.addstr(row + TILE_NROWS + 1, col, str_bottom, attr)


    # Function to draw thick gridlines around a tile at position pos (in the board coordinates)
    def _draw_wide_tile_border(self, pos:tuple, attr:int) -> None:        
        row, col = pos

        if row < 0 or row > self.board_height - TILE_NROWS - 2\
              or col < 0 or col > self.board_width - TILE_NCOLS - 2:
            raise ValueError(f"Cannot draw a tile with top-left corner at {row, col}!")

        # str_top = C_FULL + C_WIDE_T*(TILE_NCOLS) + C_FULL
        # str_space = C_FULL + ' '*(TILE_NCOLS) + C_FULL
        # str_bottom = C_FULL + C_WIDE_B*(TILE_NCOLS) + C_FULL

        str_top = C_FULL*(TILE_NCOLS + 2)
        str_space = C_FULL*2 + ' '*(TILE_NCOLS-2) + C_FULL*2
        str_bottom = C_FULL*(TILE_NCOLS + 2)

        self.board.addstr(row, col, str_top, attr)
        for i in range(TILE_NROWS):
            self.board.addstr(row + i + 1, col, str_space, attr)
        self.board.addstr(row + TILE_NROWS + 1, col, str_bottom, attr)


    # Function to add text txt to a tile at position pos (in the board coordinates)
    # This clears up the interior of the tile before adding the text
    def _add_tile_text(self, pos:tuple, txt:str, attr:int) -> None:
        row, col = pos
        format_str = f'^{TXT_WIDTH}'
        for cur_row in range(row + 1, row + TILE_NROWS + 1):
            self.board.addstr(cur_row, col + TILE_HOFFSET, " "*TXT_WIDTH, attr)
        self.board.addstr(row + TILE_VOFFSET + 1, col + TILE_HOFFSET, format(txt, format_str), attr)

    
    # Function to draw the tile at index ind = (i,j) on the board with text txt 
    # The flag draw_border indicates whether to redraw the gridlines around the tile
    def _draw_tile(self, ind:tuple, txt:str, attr:int, draw_border:bool=False, wide_border:bool=False) -> None:
        pos = self._pos_from_ind(ind)

        if draw_border:
            if wide_border:
                self._draw_wide_tile_border(pos, attr)
            else:
                self._draw_tile_border(pos, self.grid_attr, corners=self._comp_corners(ind))
        
        self._add_tile_text(pos, txt, attr)


    # Function to draw a tile that has been shifted in a horizontal or vertical direction
    # The shift direction is specified by shift_dir = 'h' or 'v' for horizontal or vertical shift
    # The magnitude of shift is indicated by shift_val, which can be positive or negative
    # It is assumed that the shift is less than the size of the tile
    # The tile also supports a reset mode, whereby previously modified borders are reset to the original state
    def _draw_shifted_tile(self, ind:tuple, txt:str, attr:int, shift_dir:chr, shift_val:int, reset:bool=False) -> None:
        row, col = self._pos_from_ind(ind)        
        
        if shift_val == 0: 
            self._draw_wide_tile_border((row, col), attr)
            self._add_tile_text((row, col), txt, attr)
            return
        
        if shift_dir == 'v' and abs(shift_val) >= TILE_NROWS + BORDER_WIDTH: 
            raise ValueError("Vertical shift greater than tile height!")
        
        if shift_dir == 'h' and abs(shift_val) >= TILE_NCOLS + BORDER_WIDTH:
            raise ValueError("Horizontal shift greater than tile width!")

        if shift_dir == 'h':  # Horizontal shift
            col += shift_val
            # tl, tr, bl, br = C_MID_U, C_MID_U, C_MID_D, C_MID_D
        elif shift_dir == 'v':  # Vertical shift
            row += shift_val            
            # tl, tr, bl, br = C_MID_L, C_MID_R, C_MID_L, C_MID_R
        else:
            raise ValueError("Invalid shift direction!")
        
        # self._draw_tile_border((row, col), self.grid_attr, corners=(tl, tr, bl, br))
        
        self._draw_wide_tile_border((row, col), attr)
        self._add_tile_text((row, col), txt, attr)
        

    # Function to add a new tile to the board at index ind = (i,j)
    def add_new_tile(self, tiles, ind, tile_id):
        self._clear_msg()
        self._draw_tile(ind, SYMBOLS[tile_id], self.new_tile_attr)
        self.board.refresh()

    # Function to draw the board for a given matrix of tiles 
    def draw_board(self, tiles):
        for i in range(self.size):
            for j in range(self.size):
                self._draw_tile((i,j), SYMBOLS[tiles[i,j]], self.tile_attr)
        self.board.refresh()


    # Function to animate the moves made by the player
    # The variable tile_moves is a list of entries of the form (staring_end, shift_dir, shift_val, merge_flag)
    # where starting_end is the starting position of the tile, shift_dir is the direction of shift ('h' or 'v')
    # shift_val is the magnitude of shift, and merge_flag is a boolean indicating whether the tile was merged
    def make_move(self, tiles, moved_tiles, move_id, tile_moves:list[tuple]):    
        
        # HELPER FUNCTIONS
        # =====================

        # Function to compute parameters related to the movement for a given shift direction
        def parse_move(tile_moves, shift_dir):
            if shift_dir == 1:
                tile_dim, step = TILE_HEIGHT,-VSTEP
                tile_moves.sort(key = lambda mov: mov[0][0])
            elif shift_dir == 2:
                tile_dim, step = TILE_WIDTH, -HSTEP    
                tile_moves.sort(key = lambda mov: mov[0][1])
            elif shift_dir == 3:
                tile_dim, step = TILE_HEIGHT, VSTEP
                tile_moves.sort(key = lambda mov: mov[0][0], reverse=True)
            elif shift_dir == 4:
                tile_dim, step = TILE_WIDTH, HSTEP    
                tile_moves.sort(key = lambda mov: mov[0][1], reverse=True)
            else:
                raise ValueError("Invalid shift direction!")
            return tile_dim, step
            

        # Function to compute the index of a tile after a shift in a given direction
        def compute_shifted_ind(ind:tuple, shift_dir:chr, shift_val:int) -> tuple:
            r,c = ind
            if shift_dir == 'v':
                return r+shift_val, c
            elif shift_dir == 'h':
                return r, c+shift_val
            else:         
                raise ValueError("Invalid shift direction!")    
            


        # MAIN FUNCTION BODY
        # =====================
        shift_dir = 'v' if move_id in [1,3] else 'h'
        tile_dim, step = parse_move(tile_moves, move_id)
        move_flags = [True for move in tile_moves]
        
        shift = 0
        x = 0
        # self.scr.addstr(0, 0, str(move_flags))
        while any(move_flags):
            shift += step

            # Compute the number of full tile and fractional shifts for a given coordinate shift
            # Setting int_shift = shift // tile_dim etc does not work, since we want the least amount of shift
            # required counting from zero. 
            int_shift = (abs(shift) // tile_dim) * sign(step)
            frac_shift = (abs(shift) % tile_dim) * sign(step)
            
            
            # Draw the tiles that are still in motion
            for i, move in enumerate(tile_moves):
                if move_flags[i]:
                    orig_ind, final_ind, merge = move
                    txt = SYMBOLS[tiles[orig_ind]]

                    # The index of the shifted tile 
                    shifted_ind = compute_shifted_ind(orig_ind, shift_dir, int_shift)
                
                    if frac_shift: 
                        # Redraw an unshifted empty tile at the previous position to erase the border
                        self._draw_tile(shifted_ind, '', self.tile_attr, draw_border=True)

                        # Draw the shifted tile 
                        self._draw_shifted_tile(shifted_ind, txt, self.mov_tile_attr, shift_dir, frac_shift)                        
                        
                    else:
                        # Redraw an unshifted empty tile at the previous position to erase the border
                        # In this case we need a tile that was shifted by one less than the current shift
                        prev_ind = compute_shifted_ind(orig_ind, shift_dir, int_shift-sign(step))
                        self._draw_tile(prev_ind, '', self.tile_attr, draw_border=True)

                        # Draw the shifted tile 
                        self._draw_shifted_tile(shifted_ind, txt, self.mov_tile_attr, shift_dir, frac_shift)

                        if shifted_ind == final_ind:
                            move_flags[i] = False
                        

            # Redraw all the tiles that have finished moving (to avoid anomalous borders)                        
            for i, move in enumerate(tile_moves):
                if not move_flags[i]:
                    orig_ind, final_ind, merge = move
                    txt = SYMBOLS[moved_tiles[final_ind]]

                    if merge:
                        self._draw_tile(final_ind, txt, self.merged_tile_attr, draw_border=True, wide_border=True)
                    else:
                        self._draw_tile(final_ind, txt, self.mov_tile_attr, draw_border=True, wide_border=True)
                                            

            self.board.refresh()
            sleep(DELAYS[shift_dir])
            # x += 1
            # self.scr.addstr(x, 0, str(move_flags))
            # self.scr.refresh()
            

        for move in tile_moves:
            if move[2]:
                txt = SYMBOLS[moved_tiles[move[1]]]             
                self._draw_tile(move[1], txt, self.merged_tile_attr, draw_border=True, wide_border = True)
            
        self.board.refresh()
        sleep(DELAYS['m'])

        for move in tile_moves:
            txt = SYMBOLS[moved_tiles[move[1]]]             
            self._draw_tile(move[1], txt, self.tile_attr, draw_border=True)

        self.board.refresh()





    # TEXT PRINTING ROUNTINES
    # =================================================================

    def _display_msg(self, msg, attr):
        self.window.addstr(self.msg_row, 1, msg.center(self.win_width-2), attr)
        self.window.refresh()


    def _clear_msg(self):
        self._display_msg("", self.msg_attr)


    def display_score(self, score):
        msg = f"{score} moves played so far"
        self.window.addstr(self.score_row, SIDE_MARGIN, msg.rjust(self.board_width), self.score_attr)
        self.window.refresh()


    def quit_game(self):
        self._display_msg("Quitting! Press any key to exit...", self.msg_attr)


    def invalid_move(self): 
        self._display_msg("CANNOT MOVE IN THAT DIRECTION!", self.err_attr)


    def gameover(self):
        self._display_msg("Game over! Press any key to exit...", self.err_attr)


    def display_msg(self, msg):
        self._display_msg(msg, self.msg_attr)



    # INPUT ROUNTINE
    # =================================================================
    def get_move(self):
        while True: 
            inp = self.scr.getch()
            if inp == curses.KEY_RESIZE:
                # self._clear_msg()
                self._display_msg("Screen resized!", self.msg_attr)
                self.resize_scr()
                continue
            elif chr(inp) in MOVE_DICT:
                # self._clear_msg()
                return MOVE_DICT[chr(inp)]
            else:
                self.display_error("Invalid key! Press w/s/a/d to move, q to quit...")
                continue
        

    def resize_scr(self):
        self.scr_height, self.scr_width = self.scr.getmaxyx()

        self.window.addstr(3, 0, f"{self.scr_height} x {self.scr_width} <---> {curses.LINES} x {curses.COLS}")
        self.window.refresh()
