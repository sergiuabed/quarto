import sys
sys.path.append('../quarto')
import numpy as np
from quarto.objects import Quarto, Piece

def custom_deepcopy(state: Quarto) -> Quarto:
    state_copy = Quarto()
    board = state.get_board_status()

    idx = [(i,j) for i in range(4) for j in range(4) if board[i,j] != -1]

    for pos in idx:
        if not state_copy.select(board[pos]):
            raise("Error when selecting!")

        if not state_copy.place(pos[1], pos[0]):
            raise("Error when placing")

    if not state.get_selected_piece() == -1:
        if not state_copy.select(state.get_selected_piece()):
            raise("Error when selecting!")

    return state_copy
