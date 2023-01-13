import sys
sys.path.append('../quarto')

from quarto.objects import *
from collections import namedtuple
import random

POPULATION_SIZE = 70
OFFSPRING_SIZE = 40
NUM_GENERATIONS = 10 #20

State = namedtuple("State", "boardState, chosenPiece")

Move = namedtuple("Move", "boardStateBeforeMove, position, pieceForNextMove")    # gene
# the piece to be played at this move is encoded in "boardStateBeforeMove"
# "position" is a (x, y) tuple indicating the coordinate where the piece should be placed

class Individual():
    def __init__(self, genome) -> None:
        self.genome = genome    # sequence of moves
        self.leaf_evaluation = None
        self.fitness = None
        self.height_reached = None   # the highest height its leaf evaluation reached throughout the reservation_tree
        self.mutated = False
        self.is_copy = False

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

def mutation(ind: Individual, state: Quarto) -> Individual:
    #pom = random.randrange(0, len(ind.genome)) # pom = Point of Mutation
    pom = random.randrange(int(len(ind.genome)/2), len(ind.genome)) # pom = Point of Mutation
    new_ind = Individual(copy.deepcopy([ ind.genome[i] for i in range(pom) ]))

    _match = custom_deepcopy(state) #copy.deepcopy(state)
    # bring _match to the state at which the agent has to play
    
    for m in new_ind.genome:
        if _match.get_selected_piece() == -1:   # check if current state is the beginning of the game
            _match.select(m.pieceForNextMove)
        else:
            _match.place(m.position[0], m.position[1])
            _match.select(m.pieceForNextMove)

    allPieces = [i for i in range(16)]
    while _match.check_winner() < 0 and not _match.check_finished():
        board = _match.get_board_status()

        freeSpots = [(i,j) for i in range(_match.BOARD_SIDE) for j in range(_match.BOARD_SIDE) if board[j, i] == -1]
        remainingPieces = [i for i in allPieces if i not in board and i != _match.get_selected_piece()]

        pickedSpot = random.choice(freeSpots)   # spot where to place the piece picked by the opponent in the previous turn

        if len(remainingPieces) != 0:   # here if statement is needed because if "remainingPieces" is empty (i.e. there are no more remaining pieces to choose for the next move), "random.choice()" raises an error
            pickedPiece = random.choice(remainingPieces)    # piece to be used in the next move, not this one!!
        else:
            pickedPiece = None  # this should not cause issues because at the next recursive call the board will be full  and "_match.check_finished()" will return true
           
        if _match.get_selected_piece() == -1:   # check if current state is the beginning of the game
            move = Move(State(_match.get_board_status(), _match.get_selected_piece()), None, pickedPiece)   # can't do any move at the beginning of the game because there is no piece picked
            _match.select(pickedPiece)
            new_ind.genome.append(move)
        else:
            move = Move(State(_match.get_board_status(), _match.get_selected_piece()), pickedSpot, pickedPiece)
            _match.place(*pickedSpot)
            _match.select(pickedPiece)
            new_ind.genome.append(move)

        new_ind.mutated = True

    return new_ind


def compare_genome_portion(genome1: list, board_states_traversed: list) -> bool:

    for i in range(len(board_states_traversed)):
        if len(genome1) < len(board_states_traversed) or not np.array_equal(genome1[i].boardStateBeforeMove.boardState, board_states_traversed[i].boardState) or not genome1[i].boardStateBeforeMove.chosenPiece == board_states_traversed[i].chosenPiece:
            return False
    #print("I've been here")
    return True

def reservation_tree(population: list, state: Quarto, board_states_traversed: list, highest_depth: int, reached_depth: int, maximizing: bool):
# "highest_depth" is the length of the genome of the individual with the longest genome
# "board_states_traversed" includes also the current state. This is useful for seeing how individuals with common initial moves diverge to different moves from the current state
# the evaluation of the leaf states can be: 0 (very unlikely), -1 (if opponent of our agent wins) or 1 (our agent wins)
    
    relevant_population = [p for p in population if len(p.genome) >= reached_depth and p.fitness == None and compare_genome_portion(p.genome, board_states_traversed)]
    # individuals have different lengths, so not all of them will reach the deepest point in the tree. This is why we have "len(p.genome) >= reached_depth"
    # "p.height_reached" indicates up to which level (from bottom up) the leaf value arrived. If it is equal to "None" it means that this individual's leaf value may still propagate upwards
    # "compare_status()" checks if the gene at level "reached_depth" (in the reservation tree) of the individual corresponds to the current state
    
    if state.check_winner() > -1 or state.check_finished():
        #print("Leaf node")
        individuals = []
        for ind in population:
            if compare_genome_portion(ind.genome, board_states_traversed):
                individuals.append(ind)
                
        if len(individuals) > 1:
            for i in range(1, len(individuals)):
                individuals[i].is_copy = True
                individuals[i].fitness = -100

        if len(individuals) < 1:
            raise Exception("PROBLEM!!!: No individual found at this leaf node of the reservation tree, but this is impossible!")

        ind = individuals[0]
        
        if state.check_winner() > -1:
            ind.leaf_evaluation = -1 if maximizing == True else 1

            return -1 if maximizing == True else 1  # fitness: if the current state is an end state, then this means that the player who played the previous turn won
                                                    # so, here if the end state happens when a maximizing move should be played, then this means that we (our agent) lost

        if state.check_finished():
            ind.leaf_evaluation = 0
            return 0    # draw; the fitness of this individual is 0

    moves_performed = []
    min_eval = 100000
    max_eval = -100000

    for ind in relevant_population:
        if (ind.genome[reached_depth].position, ind.genome[reached_depth].pieceForNextMove) not in moves_performed:
            state_copy = custom_deepcopy(state) #copy.deepcopy(state)
            board_states_traversed_copy = copy.deepcopy(board_states_traversed)

            if not np.array_equal(ind.genome[reached_depth].boardStateBeforeMove.boardState, state_copy.get_board_status()):
                raise Exception("WHAT THE HECK!!! 'reached_depth' AND GENES IN GENOMES ARE NOT ALLIGNED!!!!")

            position = ind.genome[reached_depth].position
            piece = ind.genome[reached_depth].pieceForNextMove

            moves_performed.append((position, piece))   # to avoid doing the same moves again

            if position != None:    # position == None can happen if the current state is the very beginning of the game, when the first player can only choose the piece for the opponent
                state_copy.place(*position)
            state_copy.select(piece)

            if state_copy.check_winner() == -1 and not state_copy.check_finished():
                board_states_traversed_copy.append(State(state_copy.get_board_status(), piece))

            eval = reservation_tree(relevant_population, state_copy, board_states_traversed_copy, highest_depth, reached_depth + 1, not maximizing)

            min_eval = min_eval if min_eval < eval else eval
            max_eval = max_eval if max_eval > eval else eval

    for ind in relevant_population:     # the purpose of this loop is to compute the fitness of the individuals whose leaf value stops propagating
        if maximizing and ind.leaf_evaluation != max_eval:
            ind.fitness = highest_depth - reached_depth     # the upward propagation of "leaf_evaluation" of this individual ends here

        if not maximizing and ind.leaf_evaluation != min_eval:
            ind.fitness = highest_depth - reached_depth     # the upward propagation of "leaf_evaluation" of this individual ends here

    if reached_depth == 0:
        n = [i for i in population if i.fitness == None and not i.is_copy]
        for i in n:
            i.fitness = highest_depth - reached_depth + 1

        copies = [i for i in population if i.is_copy]
        for c in copies:
            c.fitness = -100

    if maximizing:
        return max_eval

    return min_eval



def recombination(ind1: Individual, ind2: Individual) -> Individual:    # RECOMBINATION NOT USED IN THIS ALGORITHM
    pass

def initialize_population(match: Quarto) -> tuple:
    population = []
    longest_length = -1
    for l in range(POPULATION_SIZE):
        _match = custom_deepcopy(match) #copy.deepcopy(match)
        ind = Individual([])

        allPieces = [i for i in range(16)]
        while _match.check_winner() < 0 and not _match.check_finished():
            board = _match.get_board_status()

            freeSpots = [(i,j) for i in range(_match.BOARD_SIDE) for j in range(_match.BOARD_SIDE) if board[j, i] == -1]
            remainingPieces = [i for i in allPieces if i not in board and i != _match.get_selected_piece()]

            pickedSpot = random.choice(freeSpots)   # spot where to place the piece picked by the opponent in the previous turn
            
            if len(remainingPieces) != 0:   # here if statement is needed because if "remainingPieces" is empty (i.e. there are no more remaining pieces to choose for the next move), "random.choice()" raises an error
                pickedPiece = random.choice(remainingPieces)    # piece to be used in the next move, not this one!!
            else:
                pickedPiece = None  # this should not cause issues because at the next recursive call the board will be full  and "_match.check_finished()" will return true


            if _match.get_selected_piece() == -1:   # check if current state is the beginning of the game
                move = Move(State(_match.get_board_status(), _match.get_selected_piece()), None, pickedPiece)   # can't do any move at the beginning of the game because there is no piece picked
                _match.select(pickedPiece)
                ind.genome.append(move)
            else:
                move = Move(State(_match.get_board_status(), _match.get_selected_piece()), pickedSpot, pickedPiece)
                if not _match.place(*pickedSpot):
                    print("WHAT THE HECK!")
                _match.select(pickedPiece)
                ind.genome.append(move)
        
        longest_length = longest_length if longest_length > len(ind.genome) else len(ind.genome)

        population.append(ind)

    return population, longest_length

def tournament(population: list, tournament_size:int =20) -> Individual:
    return max(random.choices(population=population, k=tournament_size), key=lambda i: i.fitness)

def evolution(population: list, longest_length: int, state: Quarto) -> list:
    offspring = []
    chosen_one = None
    for g in range(NUM_GENERATIONS):
        print(f"GEN = {g}")
        offspring = []

        count = 0
        for ind in population:
            if ind.fitness == None:
                count += 1

        if count > 0:
            print(f"THIS SHOULD NOT HAPPEN!! count = {count}")   
            raise(f"THIS SHOULD NOT HAPPEN!! count = {count}")

        for i in range(OFFSPRING_SIZE):
            p = tournament(population)
            o = mutation(p, state)
            offspring.append(o)
        population += offspring

        count_negative = 0
        for ind in population:  # reset fitness of population to None
            if ind.fitness == -100:
                count_negative += 1
            ind.fitness = None

        state_copy = custom_deepcopy(state) #copy.deepcopy(state)
        reservation_tree(population, state_copy, [State(state_copy.get_board_status(), state_copy.get_selected_piece())], longest_length, 0, True)

        for ind in population:
            if ind.fitness == None:
                raise("THIS SHOULD NOT HAPPEN!!")

        population_win = []
        population_lose = []
        population_draw = []
        for i in population:
            if i.leaf_evaluation == 1:
                population_win.append(i)
            if i.leaf_evaluation == -1:
                population_lose.append(i)
            if i.leaf_evaluation == 0:
                population_draw.append(i)

        size_win = len(population_win)
        size_lose = len(population_lose)
        final_population = []   # purpose of this is to have an equilibrate nr of individuals resulting in win and the ones resulting in losing
        if size_win > POPULATION_SIZE/2:
            final_population += sorted(population_win, key = lambda i: i.fitness, reverse = True)[:int(POPULATION_SIZE/2)]
        else:
            final_population += sorted(population_win, key = lambda i: i.fitness, reverse = True)[:size_win]

        if size_lose > POPULATION_SIZE/2:
            final_population += sorted(population_lose, key = lambda i: i.fitness, reverse = True)[:int(POPULATION_SIZE/2)]
        else:
            final_population += sorted(population_lose, key = lambda i: i.fitness, reverse = True)[:size_lose]
        
        final_population += population_draw

        final_population = sorted(population, key = lambda i: i.fitness, reverse = True)[:POPULATION_SIZE]

        if g == NUM_GENERATIONS - 1:
            if size_win > 0:
                chosen_one = sorted(population_win, key = lambda i: i.fitness, reverse = True)[0]
            else:
                if len(population_draw) > 0:
                    chosen_one = sorted(population_draw, key = lambda i: i.fitness, reverse = True)[0]
                else:
                    chosen_one = sorted(population_lose, key = lambda i: i.fitness, reverse = False)[0]

    return chosen_one