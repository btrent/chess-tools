#!/usr/bin/python

import os
import re
import sys

# pylint: disable=C0103
year = "0"

def main():
    global year

    if not os.path.exists(os.path.dirname("sorted")):
        os.mkdir("sorted")

    status = 0
    line = ""
    game = {}
    passed_first_game = 0
    bracket_str = re.compile(r"^\[[A-Za-z][A-Za-z0-9]+ \".*?\"\]")
    event_str = re.compile(r"^\[Event ")
    date_str = re.compile(r"^\[Date \".*(\d\d\d\d)")
    space = re.compile(r"^ +$")

    if len(sys.argv) != 2:
        print "USAGE: sort_by_year <input file> \
            \n\nExample: sort_by_year test.pgn\n"
        sys.exit(0)

    filename = sys.argv[1]
    filehandle = open(filename, 'r')

    for row in filehandle.readlines():
        row = row.rstrip('\n')
        row = row.rstrip('\r')
        date_match = date_str.match(row)
        if date_match:
            year = date_match.group(1)

        if event_str.match(row):
            status = status + 1
            if status % 100000 == 0:
                print "Processed " + str(status) + " games."
            # don't process on line 1
            if passed_first_game == 1:
                game["moves"] = line
                process_game(game)
                year = "0"
                line = ""
                game = {}
            passed_first_game = 1

        if bracket_str.match(row):
            row = row.replace('[', '')
            row = row.replace('"]', '')
            tag = row.split(" \"", 2)
            try:
                game[tag[0]] = tag[1]
            except:
                print "Bad tag!"
                print "\""+row+"\""
                sys.exit(1)

        #if ((not bracket_str.match(row)) and (not space.match(row))
        elif (not space.match(row)) and (len(row) > 0):
            # if the line does not end with a space (required between moves) and
            # also does not end with a dot (a move already began), add a space
            if row[-1] != " " and row[-1] != ".":
                row += " "
            line += row

    #final one doesn't trigger by seeing a new game
    game["moves"] = line
    process_game(game)
    year = "0"
    line = ""
    game = {}

    filehandle.close()

def process_game(game):
    with open("./sorted/"+year+".pgn", "a") as pgn:
        pgn.write(print_game(game))

def print_game(game):
    if game["Event"] is None:
        return ""

    game_text = ""

    game_text = game_text + "[Event \""+game["Event"]+"\"]\n"
    for key in game.keys():
        if key == "moves" or key == "Event":
            continue
        game_text = game_text + "["+key+" \""+game[key]+"\"]\n"

    game_text = game_text + "\n" + game["moves"] + "\n\n"

    return game_text

if __name__ == "__main__":
    main()
