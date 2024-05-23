import subprocess
import math


# This function runs a nuxmv file with file as input and saves the input.
def nuXmv_running(name_model):
    nuXmv_proc = subprocess.Popen(["nuXmv", name_model], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  universal_newlines=True)  # Open the process
    out_file = name_model.split(".")[0] + ".out"  # Create the name for new file, the model name with extension: .out
    stdout, _ = nuXmv_proc.communicate()
    with open(out_file, "w") as file:  # Open the file in order to write in it.
        file.write(stdout)
    print("Saved in:" + out_file)

    return out_file


# This function gets a board in smv and parsing it.
def board_parsing(board_str):
    lines = board_str.split('\n')
    board = [list(line.strip()) for line in lines if line.strip()]
    return board


# This function gets a board and the place (x,y) and returns whether it is valid or not.
def place_validation(c, r, board):
    row = len(board)
    col = len(board[0])
    return 0 <= c and c < col and 0 <= r and r < row and board[r][c] != '#'


# This function gets a board and the place (x,y) of the keeper and returns whether it is valid or not.
def keeper_validation(c, r, board):
    return place_validation(c, r, board) and board[r][c] != '*' and board[r][c] != '$'


# This function returns the stinig that writes the VAR part.
def vars(board, col, row):
    add_str = ""
    for r in range(row):
        for c in range(col):
            if board[r][c] != '#':
                add_str += f"    position_{r}_{c} : 1..3;\n"
    add_str += f"    steps : 0..60;\n"

    return add_str


# This function returns the string that writes the INIT part.
def initials(board, col, row):
    add_str = ""
    init_state = []
    for r in range(row):
        for c in range(col):
            if board[r][c] == '_':
                init_state.append(f"position_{r}_{c} = 1")
            elif board[r][c] == '.':
                init_state.append(f"position_{r}_{c} = 1")
            elif board[r][c] == '$':
                init_state.append(f"position_{r}_{c} = 2")
            elif board[r][c] == '*':
                init_state.append(f"position_{r}_{c} = 2")
            elif board[r][c] == '@':
                init_state.append(f"position_{r}_{c} = 3")
            elif board[r][c] == '+':
                init_state.append(f"position_{r}_{c} = 3")
    add_str += " & ".join(init_state)
    add_str += f" & steps = 0\n"  # Starts with 0 steps.

    return add_str


# This function returns the string that writes the TRANS part.
def trans(board, col, row):
    add_str = f"   case\n"
    trans = []  # List of transitions, at first empty.
    true_cases = [f"       TRUE:\n"]  # List of true cases.
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Possible directions.

    for r in range(row):
        for c in range(col):
            if keeper_validation(c, r, board):
                for change_c, change_r in dirs:
                    new_c, new_r = c + change_c, r + change_r
                    if place_validation(new_c, new_r, board):
                        trans.append(f"    (steps < 60 & position_{r}_{c} = 3 & position_{new_r}_{new_c} = 1):\n")
                        trans.append(
                            f"       next(position_{r}_{c}) = 1 &\n       next(position_{new_r}_{new_c}) = 3 &\n       next(steps) = steps + 1 \n")
                        for rr in range(row):
                            for cc in range(col):
                                if not (rr == r and cc == c) and not (rr == new_r and cc == new_c) and place_validation(
                                        cc, rr, board):
                                    trans.append(f"       & next(position_{rr}_{cc}) = position_{rr}_{cc} \n")
                        trans.append(';')
                        if keeper_validation(c + 2 * change_c, r + 2 * change_r, board):
                            nnew_c, nnew_r = c + 2 * change_c, r + 2 * change_r
                            trans.append(
                                f"    (steps < 60 & position_{r}_{c} = 3 & position_{new_r}_{new_c} = 2 & position_{nnew_r}_{nnew_c} = 1):\n")
                            trans.append(
                                f"       (next(position_{r}_{c}) = 1 &\n       next(position_{new_r}_{new_c}) = 3 &\n       next(position_{nnew_r}_{nnew_c}) = 2 &\n       next(steps) = steps + 1);\n")
            if place_validation(c, r, board):
                true_cases.append(f"       (next(position_{r}_{c}) = position_{r}_{c})&")

    true_cases.append(f"       (next(steps) = steps);")
    add_str += "".join(trans) + "\n"
    add_str += " \n ".join(true_cases) + "\n" + "   esac;\n"

    return add_str


# This function returns the string that writes the ltl part.
def ltlspec(board, col, row):
    add_str = ""
    stars = []
    for r in range(row):
        for c in range(col):
            if board[r][c] == '.':
                stars.append((r, c))
    for num, (r, c) in enumerate(stars):
        if num > 0:
            add_str += " & "
        add_str += f"(position_{r}_{c} = 2)"
    add_str += "));\n"

    return add_str


# This function gets a board and makes it an smv board.
def SMV_making(board):
    row = len(board)
    col = len(board[0])

    to_model_SMV = f"MODULE main\n"  # First line in an smv file.
    to_model_SMV += f"VAR\n"  # Title for VARS:
    to_model_SMV += vars(board, col, row)  # Add the vars.
    to_model_SMV += f"INIT\n"  # Title for INITS:
    to_model_SMV += initials(board, col, row)  # Add the initials.
    to_model_SMV += f"TRANS\n"  # Title for TRANS:
    to_model_SMV += trans(board, col, row)  # Add the transitions.
    to_model_SMV += f"LTLSPEC\n   ! (F ("  # Title for LTLSPEC:
    to_model_SMV += ltlspec(board, col, row)  # Add the ltls.

    return to_model_SMV


# This function will solve the board
def board_solving(board_str):
    board = board_parsing(board_str)  # Parse the board.
    to_model_SMV = SMV_making(board)  # Make SMV.
    name_model = "sokoban.smv"

    model_file = open(name_model, "w")  # Open the file to write to it.
    model_file.write(to_model_SMV)
    model_file.close()

    out_file = nuXmv_running(name_model)  # Running the nuXmv file.

    temp_file = open(out_file, "r")  # Open the file to read the output.
    output = temp_file.read()

    if "is true" in output:
        print("Board is not winnable!")  # Not able to win.
    else:
        print("Board is winnable.")  # Can win.


board_xsb = """\
#####
#$@.#
#####
"""

board_solving(board_xsb)
