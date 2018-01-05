#!/usr/bin/python
# -*- coding: utf-8 -*-

import chess
import pgn
import pycurl
from StringIO import StringIO
import subprocess 
import sys
import time
import unicodedata
import urllib

memberid = MEMBERID
username = USERNAME
password = PASSWORD

login_url = "http://www.chess-server.net/user/login"
buffer = StringIO()
c = pycurl.Curl()

white_player = ''
black_player = ''

def main():
    line_to_play = get_pgn()
    get_lss_games(line_to_play)

def get_pgn():
    global white_player
    global black_player

    p = subprocess.Popen(['pbpaste'], stdout=subprocess.PIPE)
    p.wait()
    pgn_text = p.stdout.read().replace('\r','\n')
    game = pgn.PGNGame()
    game = pgn.loads(pgn_text)[0]

    white_player = game.white.split(',')[0]
    black_player = game.black.split(',')[0]

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

def get_lss_games(line_to_play):
    global buffer
    global c
    global login_url
    global username
    global password
    global white_player
    global black_player

    # 
    # Step 1: Login
    #

    c.setopt(c.URL, login_url)
    c.setopt(pycurl.TIMEOUT, 10)
    c.setopt(pycurl.FOLLOWLOCATION, 1)
    c.setopt(c.WRITEDATA, buffer)

    c.setopt(pycurl.POSTFIELDS, 'username='+username+'&password='+password+'&rememberMe=0&referer=http%3A%2F%2Fwww.chess-server.net%2Ftournaments%2Fcrosstable%2Ftourid%2F36623&commit=Submit')
    c.setopt(pycurl.COOKIEJAR, 'cookie.txt')
    #c.setopt(c.VERBOSE, True)

    c.perform()

    body = buffer.getvalue()

    #
    # Step 2: Load each game page
    #
    c.reset()
    c.setopt(pycurl.TIMEOUT, 10)
    c.setopt(pycurl.FOLLOWLOCATION, 1)
    c.setopt(c.WRITEDATA, buffer)

    # grab lines like <input style="width:5pc;font-size:80%" value="Move" type="button" onclick="document.location.href='/games/movegame/gameid/326447';" /> 
    lines = body.splitlines()
    gameid = None
    white_name = None
    black_name = None
    for line in lines:
        if 'value="Move" type="button"' in line:
            time.sleep(3)
            index = line.index("location.href")
            gameid = line[index+38:index+44]
            # TODO this will break when 1MM games are played on the LSS
            # This should not happen before 2025
            game_url = "http://www.chess-server.net" + line[index+15:index+44]
            c.setopt(c.URL, game_url)
            c.perform()

            body = buffer.getvalue()

            #
            # Step 3: Extract FEN from each game page
            #

            # grab lines like: <input type="hidden" name="DOWNLOADFEN" id="DOWNLOADFEN" value="r1bqkb1r/1pp2ppp/6n1/pP2n3/2Pp4/P4N2/1B2PPPP/RN1QKB1R w KQkq - 0 9" readonly="readonly" />
            lines = body.splitlines()
            fen = ""
            for line in lines:
                if '<h3>Game' in line:
                    # <h3>Game 351865: Trent - Dehaybe </h3>
                    tmp = line.split(' ')
                    white_name = make_ascii(tmp[2])
                    black_name = make_ascii(tmp[4])

                if 'id="DOWNLOADFEN" ' in line:
                    # Ugly and convoluted but I really don't need to be debugging regex issues
                    # when this breaks unexpectedly in 6 months
                    index = line.index("value=")
                    line_end = line[index+7:len(line)]
                    index = line_end.index('"')
                    fen = line_end[0:index]

            if fen is not None and fen is not '':
                i = 0
                make_this_move = False
                tmp = fen.split(' ')
                fen_base = tmp[0] + ' ' + tmp[1] 
                # Necessary because LSS generates incorrect FEN strings
                board = chess.Board()
                for move in line_to_play:
                    i = i + 1
                    board.push_san(move)
                    if make_this_move is True:
                        check_move(gameid, line_to_play, board, white_name, black_name, format_move(move, i), fen)
                        return
                    btmp = board.fen().split(' ')
                    bfen = btmp[0] + ' ' + btmp[1]
                    if ((fen_base == bfen) and (white_player == white_name) and (black_player == black_name)):
                        make_this_move = True

    c.close()

def make_ascii(player_name):
    encoding = "utf-8"
    unicode_name = player_name.decode(encoding)
    return u"".join([c for c in unicodedata.normalize('NFKD', unicode_name) if not unicodedata.combining(c)])

def format_move(move, i):
    move_num = int(i/2)
    if i%2 == 0:
        delim = "..."
    else:
        move_num = move_num + 1
        delim = "."

    return str(move_num) + delim + move

def check_move(gameid, line_to_play, board, white_name, black_name, move_txt, lss_fen):
    if "=" in move_txt:
        print "Promoting is not currently supported."
        print "Bailing out!"
        sys.exit(0)

    san = board.pop()
    from_square = str(san)[0:2]
    to_square = str(san)[2:4]

    boarddir = '1'
    moving_side = 'W'
    if '...' in move_txt:
        moving_side = 'B'
        boarddir = '-1'

    print "Current line is " + str(line_to_play)
    print "Going to play " + move_txt + " in " + white_name + " - " + black_name
    y_n = raw_input('Is this correct (Y/N)?')

    if (y_n.lower() == 'y'):
        make_move(gameid, from_square, to_square, boarddir, moving_side, lss_fen, move_txt)
    else:
        print "Bailing out!"
        sys.exit(0)

def make_move(gameid, from_square, to_square, boarddir, moving_side, lss_fen, move_txt):
    global buffer
    global c
    global memberid

    castle = "none"
    if "O-O-O" in move_txt:
        castle = "queen"
    elif "O-O" in move_txt:
        castle = "king"

    post_params = 'gamemode=move&gameid='+gameid+'&gamets=admin&memberid='+memberid+'&condmove=&MAKEMOVE=Make%20Move&personalnotes=&boarddir='+str(boarddir)+'&From='+get_lss_square_number(from_square)+'&To='+get_lss_square_number(to_square)+'&Castle='+castle+'&MovingSide='+moving_side+'&Promotion=&MOVE='+from_square+'&TO='+to_square+'&DOWNLOADFEN='+urllib.quote(lss_fen.encode('utf-8'))+'&Result=running'

    c.reset()
    c.setopt(pycurl.TIMEOUT, 10)
    c.setopt(pycurl.FOLLOWLOCATION, 1)
    c.setopt(c.WRITEDATA, buffer)
    c.setopt(c.URL, 'http://www.chess-server.net/games/evaluate')
    c.setopt(pycurl.POSTFIELDS, post_params)

    print '\nPOST params\n' + post_params

    time.sleep(3)
    c.perform()
    
    body = buffer.getvalue()
    lines = body.splitlines()
    problem = False
    for line in lines:
        if problem is True:
            if (line.lstrip().rstrip() == '</div>'):
                # Empty flash div
                problem = False
            else:
                #Flash div should contain error message
                line = line.replace('</div>', '').rstrip()
                print "Problem: " + line
                sys.exit(0)
        if '<div id="flash">' in line:
            problem = True

    if problem is False:
        print "\nSuccess!"

    sys.exit(0)

# I don't understand these numbers. They are not ICCF numeric notation. Anyway, I mapped them.
def get_lss_square_number(move):
    squares = {}
    squares['a1'] = '000'
    squares['b1'] = '001'
    squares['c1'] = '002'
    squares['d1'] = '003'
    squares['e1'] = '004'
    squares['f1'] = '005'
    squares['g1'] = '006'
    squares['h1'] = '007'
    squares['a2'] = '016'
    squares['b2'] = '017'
    squares['c2'] = '018'
    squares['d2'] = '019'
    squares['e2'] = '020'
    squares['f2'] = '021'
    squares['g2'] = '022'
    squares['h2'] = '023'
    squares['a3'] = '032'
    squares['b3'] = '033'
    squares['c3'] = '034'
    squares['d3'] = '035'
    squares['e3'] = '036'
    squares['f3'] = '037'
    squares['g3'] = '038'
    squares['h3'] = '039'
    squares['a4'] = '048'
    squares['b4'] = '049'
    squares['c4'] = '050'
    squares['d4'] = '051'
    squares['e4'] = '052'
    squares['f4'] = '053'
    squares['g4'] = '054'
    squares['h4'] = '055'
    squares['a5'] = '064'
    squares['b5'] = '065'
    squares['c5'] = '066'
    squares['d5'] = '067'
    squares['e5'] = '068'
    squares['f5'] = '069'
    squares['g5'] = '070'
    squares['h5'] = '071'
    squares['a6'] = '080'
    squares['b6'] = '081'
    squares['c6'] = '082'
    squares['d6'] = '083'
    squares['e6'] = '084'
    squares['f6'] = '085'
    squares['g6'] = '086'
    squares['h6'] = '087'
    squares['a7'] = '096'
    squares['b7'] = '097'
    squares['c7'] = '098'
    squares['d7'] = '099'
    squares['e7'] = '100'
    squares['f7'] = '101'
    squares['g7'] = '102'
    squares['h7'] = '103'
    squares['a8'] = '112'
    squares['b8'] = '113'
    squares['c8'] = '114'
    squares['d8'] = '115'
    squares['e8'] = '116'
    squares['f8'] = '117'
    squares['g8'] = '118'
    squares['h8'] = '119'

    return squares[move]
    

if __name__ == "__main__":
    main()
