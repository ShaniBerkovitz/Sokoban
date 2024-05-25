import subprocess
import math
import time


def nuXmv_running(model_filename):
    nuxmv_process = subprocess.Popen(["nuXmv", model_filename], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     universal_newlines=True)
    output_filename = model_filename.split(".")[0] + ".out"
    stdout, _ = nuxmv_process.communicate()

    with open(output_filename, "w") as f:
        f.write(stdout)
    return output_filename


def board_parsing(board_str):
    lines = board_str.split('\n')
    board = [list(line.strip()) for line in lines if line.strip()]
    return board


# This function gets a board and the place (x,y) and returns whether it is valid or not.
def place_validation(c, r, board):
    row = len(board)
    col = len(board[0])
    return 0 <= c < col and 0 <= r < row and board[r][c] != '#'


# This function gets a board and the place (x,y) of the keeper and returns whether it is valid or not.
def keeper_validation(c, r, board):
    return place_validation(c, r, board) and board[r][c] != '*' and board[r][c] != '$'


def trans(board, n, m, steps_limit):
    smv_model = '   case\n'
    transitions = []
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    true_list = [f"       TRUE:\n"]
    for y in range(n):
        for x in range(m):
            if keeper_validation(x, y, board):
                for dx, dy in directions:
                    nx, ny = x + dx, y + dy
                    if place_validation(nx, ny, board):
                        transitions.append(
                            f"    (steps_counter < {steps_limit} & pos_{y}_{x} = 3 & pos_{ny}_{nx} = 1):\n")
                        transitions.append(
                            f"       next(pos_{y}_{x}) = 1 &\n       next(pos_{ny}_{nx}) = 3 &\n       next(steps_counter) = steps_counter + 1 \n")
                        for i in range(n):
                            for j in range(m):
                                if not (i == y and j == x) and not (i == ny and j == nx) and place_validation(j, i,
                                                                                                              board):
                                    transitions.append(f"       & next(pos_{i}_{j}) = pos_{i}_{j} \n")
                        transitions.append(';')
                        if keeper_validation(x + 2 * dx, y + 2 * dy, board):
                            nnx, nny = x + 2 * dx, y + 2 * dy
                            transitions.append(
                                f"    (steps_counter < {steps_limit} & pos_{y}_{x} = 3 & pos_{ny}_{nx} = 2 & pos_{nny}_{nnx} = 1):\n")
                            transitions.append(
                                f"       (next(pos_{y}_{x}) = 1 &\n       next(pos_{ny}_{nx}) = 3 &\n       next(pos_{nny}_{nnx}) = 2 &\n       next(steps_counter) = steps_counter + 1);\n")

            if place_validation(x, y, board):
                true_list.append(f"       (next(pos_{y}_{x}) = pos_{y}_{x})&")

    true_list.append(f"       (next(steps_counter) = steps_counter);")
    smv_model += "".join(transitions) + "\n"
    smv_model += " \n ".join(true_list) + "\n"
    smv_model += "   esac;\n"
    return smv_model


def SMV_making(board, goal_coords, steps_limit):
    n = len(board)
    m = len(board[0])

    smv_model = f"MODULE main\nVAR\n"

    for i in range(n):
        for j in range(m):
            if board[i][j] != '#':
                smv_model += f"    pos_{i}_{j} : 1..3;\n"
    smv_model += f"    steps_counter : 0..{steps_limit};\n"

    smv_model += f"INIT\n"
    init_state = []
    for i in range(n):
        for j in range(m):
            if board[i][j] == '_':
                init_state.append(f"pos_{i}_{j} = 1")
            elif board[i][j] == '$':
                init_state.append(f"pos_{i}_{j} = 2")
            elif board[i][j] == '@':
                init_state.append(f"pos_{i}_{j} = 3")
            elif board[i][j] == '.':
                init_state.append(f"pos_{i}_{j} = 1")
            elif board[i][j] == '*':
                init_state.append(f"pos_{i}_{j} = 2")
            elif board[i][j] == '+':
                init_state.append(f"pos_{i}_{j} = 3")

    smv_model += " & ".join(init_state)
    smv_model += f" & steps_counter = 0\n"

    smv_model += f"TRANS\n"
    smv_model += trans(board, n, m, steps_limit)
    # transitions = []
    # directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    #
    # true_list = []
    # true_list.append(f"       TRUE:\n")
    # for y in range(n):
    #     for x in range(m):
    #         if keeper_validation(x, y, board):
    #             for dx, dy in directions:
    #                 nx, ny = x + dx, y + dy
    #                 if place_validation(nx, ny, board):
    #                     transitions.append(
    #                         f"    (steps_counter < {steps_limit} & pos_{y}_{x} = 3 & pos_{ny}_{nx} = 1):\n")
    #                     transitions.append(
    #                         f"       next(pos_{y}_{x}) = 1 &\n       next(pos_{ny}_{nx}) = 3 &\n       next(steps_counter) = steps_counter + 1 \n")
    #                     for i in range(n):
    #                         for j in range(m):
    #                             if not (i == y and j == x) and not (i == ny and j == nx) and place_validation(j, i,
    #                                                                                                           board):
    #                                 transitions.append(f"       & next(pos_{i}_{j}) = pos_{i}_{j} \n")
    #                     transitions.append(';')
    #                     if keeper_validation(x + 2 * dx, y + 2 * dy, board):
    #                         nnx, nny = x + 2 * dx, y + 2 * dy
    #                         transitions.append(
    #                             f"    (steps_counter < {steps_limit} & pos_{y}_{x} = 3 & pos_{ny}_{nx} = 2 & pos_{nny}_{nnx} = 1):\n")
    #                         transitions.append(
    #                             f"       (next(pos_{y}_{x}) = 1 &\n       next(pos_{ny}_{nx}) = 3 &\n       next(pos_{nny}_{nnx}) = 2 &\n       next(steps_counter) = steps_counter + 1);\n")
    #
    #         if place_validation(x, y, board):
    #             true_list.append(f"       (next(pos_{y}_{x}) = pos_{y}_{x})&")
    #
    # true_list.append(f"       (next(steps_counter) = steps_counter);")
    # smv_model += "".join(transitions) + "\n"
    # smv_model += " \n ".join(true_list) + "\n"
    # smv_model += "   esac;\n"

    smv_model += f"LTLSPEC\n   ! (F (pos_{goal_coords[0]}_{goal_coords[1]} = 2));\n"

    return smv_model


def sokoban_iterative(board_str):
    board = board_parsing(board_str)
    boxes = [(i, j) for i in range(len(board)) for j in range(len(board[0])) if board[i][j] in ['$', '*']]
    goals = [(i, j) for i in range(len(board)) for j in range(len(board[0])) if board[i][j] in ['.', '*', '+']]

    steps_limit = 50  # You can adjust this limit as needed
    total_iterations = 0
    start_time = time.time()

    for box, goal in zip(boxes, goals):
        smv_model = SMV_making(board, goal, steps_limit)
        # model_filename = "sokoban_iterative.smv"
        model_filename = f"sokoban_iterative_{input('Enter name: ')}.smv"
        with open(model_filename, "w") as f:
            f.write(smv_model)

        iteration_start_time = time.time()
        output_filename = nuXmv_running(model_filename)
        iteration_end_time = time.time()
        total_iterations += 1

        with open(output_filename, "r") as f:
            output_str = f.read()

        if "is true" in output_str:
            print(f"Iteration {total_iterations}: Box in place {box} to Goal in place {goal} - is Not Winnable!")
        else:
            print(f"Iteration {total_iterations}: Box in place {box} to Goal in place {goal} - is Winnable!")

        print(f"Iteration {total_iterations} Runtime: {iteration_end_time - iteration_start_time:.4f} seconds")

    end_time = time.time()
    print(f"Total Iterations: {total_iterations}")
    print(f"Total Runtime: {end_time - start_time:.4f} seconds")


# Example Sokoban board in XSB format

board_xsb = """\
#######
#@#####
#$----#
#.-$-.#
##-$-.#
#######
"""
# Solve Sokoban board iteratively
sokoban_iterative(board_xsb)
