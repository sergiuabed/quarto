# Free for personal or classroom use; see 'LICENSE.md' for details.
# https://github.com/squillero/computational-intelligence

import logging
import argparse
import random
import quarto
from genetic_minmax.agent import GeneticMinMaxPlayer
from monte_carlo_TS.mcts_agent import MCTSPlayer


class RandomPlayer(quarto.Player):
    """Random player"""

    def __init__(self, quarto: quarto.Quarto) -> None:
        super().__init__(quarto)

    def choose_piece(self) -> int:
        return random.randint(0, 15)

    def place_piece(self) -> tuple[int, int]:
        return random.randint(0, 3), random.randint(0, 3)


def main():
    count_0_win = 0
    count_1_win = 0
    NR_GAMES = 10
    for i in range(NR_GAMES):
        game = quarto.Quarto()
        #game.set_players((RandomPlayer(game), RandomPlayer(game)))
        #game.set_players((GeneticMinMaxPlayer(game), RandomPlayer(game)))
        game.set_players((MCTSPlayer(game), RandomPlayer(game)))
        #game.set_players((RandomPlayer(game), MCTSPlayer(game)))
        winner = game.run()
        logging.warning(f"main: Winner: player {winner}")

        if winner == 0:
            count_0_win += 1

        if winner == 1:
            count_1_win += 1    # not correct to measure it as "10-count_0_win" because there may be draws

    print("Win-rates:")
    print(f"Player 0: {count_0_win}")
    print(f"Player 1: {count_1_win}")
    print(f"Draws: {NR_GAMES-count_0_win-count_1_win}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='count',
                        default=0, help='increase log verbosity')
    parser.add_argument('-d',
                        '--debug',
                        action='store_const',
                        dest='verbose',
                        const=2,
                        help='log debug messages (same as -vv)')
    args = parser.parse_args()

    if args.verbose == 0:
        logging.getLogger().setLevel(level=logging.WARNING)
    elif args.verbose == 1:
        logging.getLogger().setLevel(level=logging.INFO)
    elif args.verbose == 2:
        logging.getLogger().setLevel(level=logging.DEBUG)

    main()