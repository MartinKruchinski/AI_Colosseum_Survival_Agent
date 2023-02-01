# Student agent: Add your own agent here
from agents.agent import Agent
from store import register_agent
import sys
import random
import math
from copy import deepcopy
import time
import random


@register_agent("student_agent")
class StudentAgent(Agent):
    """
    A dummy class for your implementation. Feel free to use this class to
    add any helper functionalities needed for your agent.
    """

    def __init__(self):
        super(StudentAgent, self).__init__()
        self.name = "StudentAgent"
        self.dir_map = {
            "u": 0,
            "r": 1,
            "d": 2,
            "l": 3,
        }
        self.autoplay = True

    def step(self, chess_board, my_pos, adv_pos, max_step):
        """
        Implement the step function of your agent here.
        You can use the following variables to access the chess board:
        - chess_board: a numpy array of shape (x_max, y_max, 4)
        - my_pos: a tuple of (x, y)
        - adv_pos: a tuple of (x, y)
        - max_step: an integer
        You should return a tuple of ((x, y), dir),
        where (x, y) is the next position of your agent and dir is the direction of the wall
        you want to put on.
        Please check the sample implementation in agents/random_agent.py or agents/human_agent.py for more details.
        """
        possible_positions = self.BFS(my_pos, adv_pos, chess_board,
                                      max_step)  # => outputs [(((x,y), wall dir), ...), number of walls in max_step_radius]

        just_positions = possible_positions[0]  # only moves and walls, excludes number of walls in max_step radius

        refine = self.refiner(just_positions, adv_pos, chess_board,
                              max_step)  # returns best pruned moves with optimal wall and grade => [((x,y), dir, grade), ...]

        mini = self.minimax(0, refine, adv_pos, chess_board, max_step,
                            True)  # returns move with best grade => (x,y), dir

        return mini[0], int(mini[1])

    def copy_chess_board(self, chess_board):  # deepcopy of chessboard
        return deepcopy(chess_board)

    def number_of_walls(self, cur_pos, adv_pos, chess_board, max_step):
        return self.BFS(cur_pos, adv_pos, chess_board, max_step)[1]  # returns number of walls in max_step radius

    def BFS(self, start_pos, adv_pos, chess_board, max_step):

        if start_pos[0] == adv_pos[0] and start_pos[1] == adv_pos[1]:  # checks if positions are same
            return False

        moves = ((-1, 0), (0, 1), (1, 0), (0, -1))
        # r-1 => up
        # c + 1 => right
        # r + 1 => down
        # c -1 => left

        # in chess board:
        # 0: u
        # 1: r
        # 2: d
        # 3: l

        final_list = []

        state_queue = [(start_pos, 0)]
        visited = {tuple(start_pos)}
        is_reached = False

        while state_queue and not is_reached:

            cur_pos, cur_step = state_queue.pop(0)

            cur_r = cur_pos[0]
            cur_c = cur_pos[1]

            if cur_step == max_step:
                break  # max steps hit

            for dir, move in enumerate(moves):  # dir returns index of moves, move is whats being added to cur_pos

                if chess_board[cur_r][cur_c][dir]:
                    continue

                next_row = cur_pos[0] + move[0]
                next_col = cur_pos[1] + move[1]

                next_pos = (next_row, next_col)

                if next_pos == adv_pos or next_pos in visited:
                    continue

                visited.add(next_pos)
                state_queue.append((next_pos, cur_step + 1))

        potential_walls = 0  # everything above is from world.py

        for position in sorted(visited):  # check which walls u can put up and how many walls at each visited position
            walls = chess_board[position[0]][position[1]]
            for i in range(len(walls)):
                if not walls[i]:
                    final_list.append((position, i))  # looks like ((x,y), dir)
                else:  # if there is a wall
                    potential_walls += 1

        return final_list, potential_walls  # final list = ((0, 0), 1)

    def check_endgame(self, chess_board, wall, p0_pos, p1_pos):  # based off given code from world.py
        """
        Check if the step from player can result in an endgame in a favorable manner.
        Returns true if ending the game and the points associate each player at the time.
        """

        p0_r = p0_pos[0]
        p0_c = p0_pos[1]

        # Union-Find
        moves = ((-1, 0), (0, 1), (1, 0), (0, -1))
        board_size = len(chess_board[0])
        # Union-Find
        father = dict()
        for r in range(board_size):
            for c in range(board_size):
                father[(r, c)] = (r, c)

        def find(pos):
            if father[pos] != pos:
                father[pos] = find(father[pos])
            return father[pos]

        def union(pos1, pos2):
            father[pos1] = pos2

        for r in range(board_size):
            for c in range(board_size):
                for dir, move in enumerate(moves[1:3]):  # additional code to check for edgecases
                    if chess_board[r, c, dir + 1]:
                        continue
                    else:
                        if not (r == p0_r and c == p0_c and dir + 1 == wall):
                            if not (wall == 0 and r == p0_r - 1 and c == p0_c and dir + 1 == 2):
                                if not (wall == 1 and r == p0_r and c == p0_c + 1 and dir + 1 == 3):
                                    if not (wall == 2 and r == p0_r + 1 and c == p0_c and dir + 1 == 0):
                                        if not (wall == 3 and r == p0_r and c == p0_c - 1 and dir + 1 == 1):
                                            pos_a = find((r, c))
                                            pos_b = find((r + move[0], c + move[1]))
                                            if pos_a != pos_b:
                                                union(pos_a, pos_b)



        for r in range(board_size):
            for c in range(board_size):
                find((r, c))
        p0_r = find(tuple(p0_pos))
        p1_r = find(tuple(p1_pos))
        p0_score = list(father.values()).count(p0_r)
        p1_score = list(father.values()).count(p1_r)
        if p0_r == p1_r:
            return False, p0_score, p1_score
        player_win = None
        win_blocks = -1
        if p0_score > p1_score:
            player_win = 0
            win_blocks = p0_score
        elif p0_score < p1_score:
            player_win = 1
            win_blocks = p1_score
        else:
            player_win = -1  # Tie
        return True, p0_score, p1_score

    def set_barrier(self, cur_pos, chess_board, barrier_dir):  # applies move on copy chessboard

        # Moves (Up, Right, Down, Left)
        # self.moves = ((-1, 0), (0, 1), (1, 0), (0, -1))
        chess_board[int(cur_pos[0])][int(cur_pos[1])][int(barrier_dir)] = True
        if barrier_dir == 0:
            chess_board[cur_pos[0] - 1, cur_pos[1], 2] = True  # go up a row and set down to true

        elif barrier_dir == 1:
            chess_board[cur_pos[0], cur_pos[1] + 1, 3] = True  # go right a position and set left true

        elif barrier_dir == 2:
            chess_board[cur_pos[0] + 1, cur_pos[1], 0] = True  # go down a position and set up true

        elif barrier_dir == 3:
            chess_board[cur_pos[0] - 1, cur_pos[1] - 1, 1] = True  # go left a position and set right true
        return chess_board

    def minimax(self, depth, refined_moves, adv_pos, board, max_step, isMaximisingPlayer):  # minimax of depth 1!

        move_value = {}

        for move in refined_moves:

            # check if current move results in win
            endgame = self.check_endgame(board, move[1], move[0], adv_pos)  # this works to check base case
            if (endgame[0] and endgame[1] > endgame[2]):
                move_value[move[0], move[1]] = 100000  # give maximum score so it is picked by root

            # check if adv can win based off move you take
            new_board = self.copy_chess_board(board)
            new_board = self.set_barrier(move[0], new_board, move[1])  # apply move

            # check if opponent can take a move to end the game
            op_end_game = self.check_if_losing_move(move, adv_pos, new_board, max_step)
            if op_end_game:  # if leads to losing move
                move_value[move[0], move[1]] = -1000000
            else:  # if not an endgame move, give it same value as grade in refiner
                move_value[move[0], move[1]] = move[2]

            sort_by_value = sorted(move_value.items(), key=lambda item: item[1])[::-1]  # sort decreasing by value [1]

        best_move = sort_by_value[0][0]  # take the maximum value

        return best_move[0], best_move[1]  # return position and wall

    def check_if_losing_move(self, move, adv_pos, board,
                             max_step):  # get rid of all moves that can result in a losing game
        spec_move = move[0]

        adv_BFS = self.BFS(adv_pos, spec_move, board, max_step)[0]  # get all possible positions for adersary
        refine_BFS = self.refiner(adv_BFS, spec_move, board,
                                  max_step)  # get best moves of adversary, since were assuming it takes the best possible move

        for adv_move in refine_BFS:
            endgame = self.check_endgame(board, adv_move[1], adv_move[0], move[0])
            if endgame[0] and endgame[1] > endgame[2]:
                return True  # if opponent wins
        return False

    def refiner(self, possible_positions, adv_pos, chess_board, max_step):  # calculate best 6 possible moves

        move_and_distance = []

        for i in range(len(possible_positions)):

            endgame = self.check_endgame(chess_board, possible_positions[i][1], possible_positions[i][0], adv_pos)
            if endgame and endgame[1] > endgame[2]:  # if our agent can win
                return [((possible_positions[i][0]), possible_positions[i][1], 1000)]

            if i > 0 and possible_positions[i][0] == possible_positions[i - 1][0]:  # edge case check
                continue

            # compute distance
            move_x, move_y = possible_positions[i][0]
            adv_x, adv_y = adv_pos
            distance_to_adv_x = (adv_x - move_x) ** 2
            distance_to_adv_y = (adv_y - move_y) ** 2
            add_distance = distance_to_adv_x + distance_to_adv_y
            distance_to_adv = math.sqrt(int(add_distance))

            move_and_distance.append([possible_positions[i][0], distance_to_adv])  # looks like ((x,y), dist)

        move_and_distance = sorted(move_and_distance, key=lambda x: x[
            1])  # sort in increasing order, we want the moves with the least distance to opponent

        if len(move_and_distance) > 5:
            move_and_distance = move_and_distance[0:5] + [move_and_distance[len(
                move_and_distance) // 2]]  # get greediest first 5 moves and move in the middle in case of retreat

        move_and_grade = []
        for i in range(len(move_and_distance)):
            num_of_walls = self.number_of_walls(move_and_distance[i][0], adv_pos, chess_board,
                                                max_step)  # get number of walls in max step radius

            grade = num_of_walls * 0.4 + move_and_distance[i][1] * 0.6  # apply weighted evaluation

            move_and_grade.append((move_and_distance[i][0], grade))

        move_and_grade = sorted(move_and_grade, key=lambda x: x[1])[::-1]  # sort in decreasing order

        best_moves = []

        for i in range(len(move_and_grade)):

            move_row, move_col = move_and_grade[i][0]
            adv_row, adv_col = adv_pos

            # for when agent is right next to adv
            # check up
            if move_row - adv_row == 1 and move_col == adv_row and not chess_board[move_row][move_col][
                0]:  # check if adv is on top
                dir = 0
                best_moves.append(((move_and_grade[i][0]), dir, move_and_grade[i][1]))
                continue
            # check right
            elif move_row == adv_row and adv_row - move_col == 1 and not chess_board[move_row][move_col][
                1]:  # check if adv is to the right
                dir = 1
                best_moves.append(((move_and_grade[i][0]), dir, move_and_grade[i][1]))
                continue
            # check down
            elif adv_row - move_row == 1 and move_col == adv_row and not chess_board[move_row][move_col][
                2]:  # check if adv is under us
                dir = 2
                best_moves.append(((move_and_grade[i][0]), dir, move_and_grade[i][1]))
                continue
            # check left
            elif move_row == adv_row and move_col - adv_row == 1 and not chess_board[move_row][move_col][
                3]:  # check if adv is to the left
                dir = 3
                best_moves.append(((move_and_grade[i][0]), dir, move_and_grade[i][1]))
                continue
            else:
                # put wall based off adv_pos

                cut = (len(chess_board) // 2)

                if move_row <= cut and adv_row <= cut and not chess_board[move_row][move_col][
                    0]:  # check if were in the y lower half of the board
                    dir = 0
                    best_moves.append(((move_and_grade[i][0]), dir, move_and_grade[i][1]))
                    continue
                elif move_col > cut and adv_col > cut and not chess_board[move_row][move_col][
                    1]:  # check if were in the rightmost half of the board
                    dir = 1
                    best_moves.append(((move_and_grade[i][0]), dir, move_and_grade[i][1]))
                    continue

                elif move_row > cut and adv_row > cut and not chess_board[move_row][move_col][
                    2]:  # check if were in the y higher half of the board
                    dir = 2
                    best_moves.append(((move_and_grade[i][0]), dir, move_and_grade[i][1]))
                    continue

                elif move_col <= cut and adv_col <= cut and not chess_board[move_row][move_col][
                    3]:  # check if were in the leftmost half of the board
                    dir = 3
                    best_moves.append(((move_and_grade[i][0]), dir, move_and_grade[i][1]))
                    continue

                else:
                    for wall in range(4):
                        if chess_board[move_row][move_col][wall]:  # if none of the scenarios
                            continue
                        else:
                            dir = wall  # take closest available wall
                            best_moves.append(((move_and_grade[i][0]), dir, move_and_grade[i][1]))
                            break

        return best_moves
