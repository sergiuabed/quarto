import sys
sys.path.append('../quarto')

from quarto.objects import *
from monte_carlo_TS.monte_carlo_ts import *

# Reasoning: a turn of a player means selecting a place on the board where to place the piece chosen by the opponent and then selecting a piece
# for the opponent. So, every turn ends by selecting a piece for the opponent
# The "mcts" function is executed everytime "place_piece" is called. If this player has to do the first move, it cannot do "place_piece" because
# there is no piece previously chosen by the opponent, so it will do only "choose_piece".
class MCTSPlayer(Player):
    def __init__(self, quarto: Quarto) -> None:
        super().__init__(quarto)

        self.__quarto = quarto
        self.parent = Node(None, quarto, None)
        expand(self.parent) # the root node must be expanded before applying MCTS
        print(len(self.parent.children))
        self.mcts_executed = False
        self.position = None
        self.piece = None

    def run_mcts(self) -> None:
        self.parent = Node(None, self.__quarto, None)   # create a new root with corresponding to the current state. In future, we might reuse the same tree
        self.position, self.piece = iterate_mcts(self.parent)
        print(f"self.position: {self.position}")
        print(f"self.piece: {self.piece}")
        self.mcts_executed = True

    def choose_piece(self) -> int:
        if not self.mcts_executed:
            self.run_mcts()

        self.mcts_executed = False
        return self.piece

    def place_piece(self) -> tuple[int, int]:
        self.run_mcts()

        
        return self.position