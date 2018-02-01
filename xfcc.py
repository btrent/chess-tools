#!/usr/bin/python

import pgn
import re
import subprocess
import string
import sys
from zeep import Client

username=USERNAME
password=PASSWORD
my_player_names=["LAST, FIRST"]
white_name = None
black_name = None


def main():
    if (len(sys.argv) > 1):
        if (sys.argv[1] == 'ls'):
            if (len(sys.argv) > 2 and sys.argv[2] == '-a'):
                list_games(True)
            else:
                list_games()
        sys.exit(0)
    line_to_play = get_pgn()
    current_game = get_iccf_game(line_to_play)

def get_pgn():
    global white_name, black_name

    p = subprocess.Popen(['pbpaste'], stdout=subprocess.PIPE)
    p.wait()
    pgn_text = p.stdout.read().replace('\r','\n')
    game = pgn.PGNGame()
    game = pgn.loads(pgn_text)[0]
    white_name = make_comparable(game.white)
    black_name = make_comparable(game.black)

    moves = strip_pgn(game)
    return moves

def strip_pgn(game):
    skip=0
    moves = []
    for move in game.moves:
        if '{' in move:
            continue
        elif '(' in move:
            skip = skip + 1
            continue
        elif ')' in move:
            skip = skip - 1
        elif skip == 0 and move != '*' and '$' not in move:
            moves.append(move)

    return moves

def make_comparable(player_name):
    return filter(lambda x: x in set(string.printable), player_name)

def list_games(print_all=False):
    result = get_games()
    data = []

    for game in result:
        if (print_all is False and game.myTurn is False):
            continue
        moves = game.moves.split()
        last_move = moves[-1]
        regex = re.compile(r"\d+\.", re.IGNORECASE)
        if (not re.match(regex, last_move)):
            move_num = moves[-2].split('.')[0]
            last_move = move_num + "..." + last_move
        if (game.drawOffered is True):
            last_move = last_move + "(=)"
        message = ""
        if (game.message is not None):
            message = game.message
        data.append([game.white.split(',')[0]+"-"+game.black.split(',')[0], last_move, message])

    pretty_print(data)


def pretty_print(data):
    widths = [max(map(len, col)) for col in zip(*data)]
    print '-'*sum(widths,len(widths)*2)
    for d in data:
        t = []
        for val, width in zip(d, widths):
            if width > 95:
                val = val[0:95]
                width = 98
            t.append(val.ljust(width+3))
        print "  ".join(t)
        print '-'*sum(widths,len(widths)*2)

    print ''


def get_games():
    global username, password, white_name, black_name
    client = Client('http://www.iccf-webchess.com/XfccBasic.asmx?wsdl')
    result = client.service.GetMyGames(username, password)

    return result

def get_iccf_game(line_to_play):
    global white_name, black_name

    result = get_games()

    print "Line to play is " + str(line_to_play)

    for game in result:
        if game.moves is None:
            continue

        if (make_comparable(game.white) == white_name and
            make_comparable(game.black) == black_name and
            game.myTurn is True):
            regex = re.compile(r"\d+\.", re.IGNORECASE)
            moves = regex.sub("", game.moves)
            iccf_game_moves = moves.rstrip().lstrip().split(' ')
            if ''.join(iccf_game_moves) in ''.join(line_to_play):
                move_to_play = line_to_play[len(iccf_game_moves)]
                move_num = int(len(iccf_game_moves)/2)+1
                print "Current line is " + str(iccf_game_moves)
                print "Going to play " + format_move(move_to_play, game.white, game.black, move_num) + " in " + game.white + " - " + game.black
                y_n = raw_input('Is this correct (Y/N)?')

                if (y_n.lower() == 'y'):
                    make_move(game, move_to_play, move_num)
                else:
                    print "Bailing out!"
                    sys.exit(0)

def make_move(game, move, move_num):
    global username, password
    client = Client('http://www.iccf-webchess.com/XfccBasic.asmx?wsdl')
    result = client.service.MakeAMove(username, password, game.id, False, False, move_num, move, False, False, '')
    print result

def format_move(move_to_play, white, black, move_num):
    global my_player_names
    if white in my_player_names:
        delim = "."
    else:
        delim = "..."

    return str(move_num) + delim + move_to_play

if __name__ == "__main__":
    main()

