#!/usr/bin/python

import pgn
import re
import subprocess
import sys
from zeep import Client

username='USERID_GOES_HERE'
password='PASSWORD_GOES_HERE'
my_player_names=["LASTNAME, FIRSTNAME"]

def main():
    line_to_play = get_pgn()
    current_game = get_iccf_game(line_to_play)

def get_pgn():
    p = subprocess.Popen(['pbpaste'], stdout=subprocess.PIPE)
    p.wait()
    pgn_text = p.stdout.read().replace('\r','\n')
    game = pgn.PGNGame()
    game = pgn.loads(pgn_text)[0]

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

def get_iccf_game(line_to_play):
    global username, password
    client = Client('http://www.iccf-webchess.com/XfccBasic.asmx?wsdl')
    result = client.service.GetMyGames(username, password)

    print "Line to play is " + str(line_to_play)

    for game in result:
        if game.myTurn is True:
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

