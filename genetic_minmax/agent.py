import sys
sys.path.append('../quarto')

from quarto.objects import *
from collections import namedtuple
from genetic_minmax.genetic import *

# Reasoning: a turn of a player means selecting a place on the board where to place the piece chosen by the opponent and then selecting a piece
# for the opponent. So, every turn ends by selecting a piece for the opponent
# The evolution function is executed everytime "place_piece" is called. If this player has to do the first move, it cannot do "place_piece" because
# there is no piece previously chosen by the opponent, so it will do only "choose_piece".
class GeneticMinMaxPlayer(Player):
    def __init__(self, quarto: Quarto) -> None:
        super().__init__(quarto)
        self.__quarto = quarto
        self.evolution_executed = False
        self.board_location = None
        self.piece_chosen = None

    def run_evolution(self) -> None:
        population, longest_length = initialize_population(self.__quarto)
        #reservation_tree(population, self.__quarto, [State(self.__quarto.get_board_status(), self.__quarto.get_selected_piece())], longest_length, 0, True)
        reservation_tree(population, self.__quarto, [State(self.__quarto.get_board_status(), self.__quarto.get_selected_piece())], longest_length, 0, True)

        ind = evolution(population, longest_length, self.__quarto)

        move = ind.genome[0]
        self.board_location = move.position
        self.piece_chosen = move.pieceForNextMove
        self.evolution_executed = True

        print(move)

        init_board = np.ones(shape=(4, 4), dtype=int) * -1
        if np.array_equal(self.__quarto.get_board_status(), init_board) and self.__quarto.get_selected_piece() == -1:
            print("Why is this happening?")
        else:
            print("It's fine apparently")
            print(self.__quarto.get_board_status())
            print(self.__quarto.get_selected_piece())


    def choose_piece(self) -> int:
        if not self.evolution_executed: # in case this agent has to do the first move. Usually, when a player has to move, it first places the piece and then selects a new piece for the opponent
            self.run_evolution()
        self.evolution_executed = False

        return self.piece_chosen

    def place_piece(self) -> tuple[int, int]:
        self.run_evolution()
        return self.board_location
