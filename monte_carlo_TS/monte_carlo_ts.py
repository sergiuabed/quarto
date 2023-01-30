import sys
sys.path.append('../quarto')

from quarto.objects import *
from collections import namedtuple
import random
import numpy as np

Move = namedtuple("Move", "position, piece")

C = 2   # temperature
MCTS_ITER_NUM = 200 # nr of iterations of the algorithm

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

class Node():
    def __init__(self, parent, state: Quarto, from_move) -> None:
        self.parent = parent
        self.from_move = from_move   # this indicates what move was performed in the previous state to reach this state
        self.state = custom_deepcopy(state) #copy.deepcopy(state)
        self.moves = []
        self.children = []
        self.n = 0  # nr of visits
        self.nr_wins = 0
        self.win_rate = 0
        self.ucb = float('inf')

        self.infer_possible_moves()

    def compute_ucb(self) -> None:
        if self.n == 0 or self.parent == None: # "self.parent == None" is True if the parent is the root node
            self.ucb = float('inf')
        else:
            self.ucb = self.nr_wins/self.n + C*np.sqrt(np.log(self.parent.n)/self.n)

    def compute_avg_val(self) -> None:
        if self.n == 0:
            self.nr_wins = 0
            self.win_rate = 0
        else:
            self.win_rate = self.nr_wins/self.n

    def infer_possible_moves(self) -> None:
        board = self.state.get_board_status()
        chosen_piece = self.state.get_selected_piece()

        ix = np.ndindex(board.shape)
        ix_free = [i for i in ix if board[i] == -1]

        unused_pieces = [p for p in range(16) if p not in board and p != chosen_piece]

        if chosen_piece == -1:  # i.e. the beginning of the game. If true, our agent makes the first move, so it will only have to choose the piece for opponent
            for piece in unused_pieces:
                m = Move(None, piece)
                self.moves.append(m)
        else:
            for pos in ix_free:
                for piece in unused_pieces:
                    m = Move((pos[1], pos[0]), piece)
                    self.moves.append(m)

                if len(unused_pieces) == 0: # in case the turn before the board becomes full. This means there are no more free pieces. Only the chosen one in the previous turn
                    m = Move((pos[1], pos[0]), -100)
                    self.moves.append(m)

def expand(parent: Node) -> None:
    
    for m in parent.moves:
        next_state = custom_deepcopy(parent.state) #copy.deepcopy(parent.state)
        
        #perform move
        if m.position != None:
            if not next_state.place(*m.position):
                raise("The given position for placing the piece is not allowed!")
        
        if not next_state.select(m.piece):
            if m.piece != -100:
                raise("Cannot select this piece!")

        child = Node(parent, next_state, m)
        parent.children.append(child)

def rollout(node: Node, maximizing: bool) -> int:    # a.k.a. go random
    state_copy = custom_deepcopy(node.state) #copy.deepcopy(node.state)
    _max = maximizing

    while state_copy.check_winner() == -1 and not state_copy.check_finished():
        board = state_copy.get_board_status()
        chosen_piece = state_copy.get_selected_piece()

        ix = np.ndindex(board.shape)
        ix_free = [i for i in ix if board[i] == -1]
        unused_pieces = [p for p in range(16) if p not in board and p != chosen_piece]

        pos = random.choice(ix_free)
        if len(unused_pieces) == 0:
            piece = -100    # this can happen if there are no more unused pieces. This means that the chosenPiece is the last one (15 pieces on the board + 1 to be placed) and once it's placed it can result in Quarto! or a draw
        else:
            piece = random.choice(unused_pieces)

        if not state_copy.place(pos[1], pos[0]):
            if piece != -100:
                raise("The given position for placing the piece is not allowed!")

        if not state_copy.select(piece):
            raise("Cannot select this piece!")

        _max = not _max

    if state_copy.check_winner() == -1 and state_copy.check_finished():
        return 0    # draw

    if not _max:
        return 1    # return 1 when _max=False because it means that _max was True when Quarto! happened

    return -1

# before using this method, make sure the tree contains at least the root node with its children expanded
def mcts(parent: Node, maximizing: bool) -> int:
    
    if parent.state.check_winner() > -1: # in case leaf node is a terminal state
        v = 0 if maximizing else 1

        parent.nr_wins += v
        parent.n += 1
        parent.compute_ucb()
        parent.compute_avg_val()

        return v
    
    if parent.state.check_finished() and parent.state.check_winner() == -1:# in case leaf node is a terminal state
        parent.n += 1
        parent.compute_ucb()
        parent.compute_avg_val()
        
        return 0
    
    if len(parent.children) == 0 and parent.n == 0: # i.e. if it's a leaf node and it's never been visited
        v = rollout(parent, maximizing)
        if v == 1:
            parent.nr_wins += 1
        parent.n += 1

        parent.compute_ucb()
        parent.compute_avg_val()

        return 1 if v == 1 else 0
    
    if len(parent.children) == 0 and parent.n != 0: # i.e. if it's a leaf node, but it was visited before
        expand(parent)
        
        child = parent.children[0] # all children have ucb = inf, so no need to sort it

        v = rollout(child, not maximizing)
        if v == 1:
            child.nr_wins += 1
            parent.nr_wins += 1
        child.n += 1
        parent.n += 1

        child.compute_ucb()
        child.compute_avg_val()
        parent.compute_ucb()
        parent.compute_avg_val()

        return 1 if v == 1 else 0

    high_ucb_child = sorted(parent.children, key=lambda x: x.ucb, reverse=True)[0]

    v = mcts(high_ucb_child, not maximizing)
    
    high_ucb_child.nr_wins += v
    high_ucb_child.n += 1
    high_ucb_child.compute_ucb()
    high_ucb_child.compute_avg_val()

    return v

def iterate_mcts(parent: Node) -> tuple:
    for i in range(MCTS_ITER_NUM):
        mcts(parent, True)

    best_move = max(parent.children, key= lambda c: c.win_rate).from_move
    print(f"I'm here. I propose this ply: {(best_move.position, best_move.piece)}")

    return (best_move.position, best_move.piece)
