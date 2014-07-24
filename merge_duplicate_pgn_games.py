#!/usr/bin/python

import re
import sys

STRIP_EMPTY_GAMES = True #remove games with no moves (eg Byes from tournaments)?

# pylint: disable=C0103
games = {}
output_filename = ''

# pylint: disable=W0603
def main():
    global output_filename

    status = 0
    line = ""
    game = {}
    passed_first_game = 0
    bracket_str = re.compile(r"^\[[A-Za-z][A-Za-z0-9]+ \".*?\"\]")
    event_str = re.compile(r"^\[Event ")
    space = re.compile(r"^ +$")
    move_spaces = re.compile(r"\. ")

    if len(sys.argv) != 2:
        print "USAGE: merge_duplicate_pgn_games <input file> \
            \n\nExample: merge_duplicate_pgn_games test.pgn\n"
        sys.exit(0)

    filename = sys.argv[1]
    output_filename = filename.split('.')[0] + '_clean.pgn'

    filehandle = open(filename, 'r')
    for row in filehandle.readlines():
        row = row.rstrip('\n')
        row = row.rstrip('\r')
        if event_str.match(row):
            status = status + 1
            if status % 100000 == 0:
                print "Processed " + str(status) + " games."
            # don't process on line 1
            if passed_first_game == 1:
                line = re.sub(move_spaces, ".", line)
                game = set_moves(game, line)
                process_game(game)
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
    line = re.sub(move_spaces, ".", line)
    game = set_moves(game, line)
    process_game(game)
    line = ""
    game = {}

    filehandle.close()

    print_games()

def set_moves(game, line):
    comments = re.compile(r"{.*?}[^A-Za-z0-9()]+")

    game["moves"] = line
    game["moves_no_comments"] = re.sub(comments, '', line)
    strip_variations(game)
    strip_variables(game)
    clean_up_numbers(game)

    return game

def strip_variables(game):
    variables = re.compile(r"\$[A-Za-z0-9]+ *")
    game["moves_no_comments"] = re.sub(variables, "", game["moves_no_comments"])

def clean_up_numbers(game):
    extra_spaces = re.compile(r" +(\d+)")
    game["moves_no_comments"] = re.sub(extra_spaces, r" \1", game["moves_no_comments"])

def strip_variations(game):
    text = game["moves_no_comments"]

    if text.find("(") == -1:
        return

    open_paren = re.compile(r"\(")
    close_paren = re.compile(r"\)")
    continuation = re.compile(r" +\d+\.\.\.")
    paren_map = [0]*len(text)
    to_strip = 0
    old_to_strip = 0
    removed = 0
    start = None
    end = None

    for i in [m.start() for m in re.finditer(open_paren, text)]:
        paren_map[i] = 1
 
    for i in [m.start() for m in re.finditer(close_paren, text)]:
        paren_map[i] = -1

    for i in range(0, len(text)):
        if to_strip == 0 and start is not None and end is not None:
            start = start-removed
            end = end-removed+1
            text = text[:start]+text[end:]
            removed = removed + end - start
            start = None
            end = None

        old_to_strip = to_strip
        to_strip = to_strip + paren_map[i]
        if to_strip != 0:
            if to_strip < 1:
                # mismatched parenthesis = bad PGN
                return
            if old_to_strip == 0:
                start = i
        elif old_to_strip != 0:
            end = i

    # why doesn't python have global replace?
    text = re.sub(continuation, " ", text, 99999)

    game["moves_no_comments"] = text

def process_game(game):
    #print "MOVES NO COMMENTS"
    #print game["moves_no_comments"]

    if STRIP_EMPTY_GAMES and check_empty_game(game):
        return

    if ((games.get(game["moves_no_comments"], None) is not None) and
            is_dupe(games.get(game["moves_no_comments"]), game)):
        games[game["moves_no_comments"]] = merge_dupes(games[game["moves_no_comments"]], game)
    elif games.get(game["moves_no_comments"], None) == game["moves_no_comments"]:
        # not a dupe but moves are the same (eg different commentary)
        new_key = game["moves_no_comments"]
        matched_game = {}
        while matched_game != None:
            new_key = new_key + " "
            matched_game = games.get(new_key, None)

        games[new_key] = game
    else:
        games[game["moves_no_comments"]] = game

def check_empty_game(game):
    if (len(game["moves_no_comments"]) < 8 or
            (game["moves_no_comments"][:3] == "1-0") or
            (game["moves_no_comments"][:3] == "0-1") or
            (game["moves_no_comments"][:7] == "1/2-1/2")):

        return True
    return False

def is_dupe(game1, game2):
    year_str = re.compile(r"(\d\d\d\d)")

    # If the moves aren't the same, they're not dupes
    if game1["moves_no_comments"] != game2["moves_no_comments"]:
        return False

    # If they both have comments, and the comments are not the same, keep both
    if ((game1["moves"].find("{") > -1) and (game2["moves"].find("{") > -1) and
            game1["moves"] != game2["moves"]):
        return False

    # If they both have Date tags and the tags do not match, they're not dupes
    if ((game1.get("Date", None) is not None) and
            (game2.get("Date", None) is not None) and
            (game1.get("Date", None) != "?") and
            (game2.get("Date", None) != "?")):
        # See if the dates match
        # Else if one is only a year, see if the years match
        if game1.get("Date") != game2.get("Date"):
            year1 = year_str.match(game1.get("Date"))
            year2 = year_str.match(game2.get("Date"))
            # Why can't python tell me how many matches there are?
            try:
                if year1.group(1) != year2.group(1):
                    return False
            except:
                return False

    # If beginnings of names are different, they're not dupes
    if ((game1.get("Black", None) is not None) and
            (game2.get("Black", None) is not None) and
            (game1.get("Black", None) != "?") and
            (game2.get("Black", None) != "?") and
            game1.get("Black")[1:4] != game2.get("Black")[1:4]):
        return False
    if ((game1.get("White", None) is not None) and
            (game2.get("White", None) is not None) and
            (game1.get("White", None) != "?") and
            (game2.get("White", None) != "?") and
            game1.get("White")[1:4] != game2.get("White")[1:4]):
        return False

    return True

def merge_dupes(game1, game2):
    abbrev_name = re.compile(r".*?, *[A-Za-z][. ]*$")
    new_game = {}
    game1_only_keys = set(game1.keys()) - set(game2.keys())
    game2_only_keys = set(game2.keys()) - set(game1.keys())
    shared_keys = set(game1.keys()) - game1_only_keys - set(["moves"]) - set(["moves_no_comments"])

    if game2["moves"].find("{") > -1:
        new_game["moves"] = game2["moves"]
        new_game["moves_no_comments"] = game2["moves_no_comments"]
    else:
        new_game["moves"] = game1["moves"]
        new_game["moves_no_comments"] = game1["moves_no_comments"]

    for key in game1_only_keys:
        new_game[key] = game1[key]
    for key in game2_only_keys:
        new_game[key] = game2[key]

    for key in shared_keys:
        if game1[key] is None or game1[key] == '' or game1[key] == '\r' or game1[key][0] == "?":
            new_game[key] = game2[key]
        elif (key == "White" or key == "Black") and abbrev_name.match(game1[key]):
            new_game[key] = game2[key]
        else:
            new_game[key] = game1[key]

    return new_game

def print_games():
    filehandle = open(output_filename, 'w')

    for game in games.keys():
        if games[game]["Event"] is None:
            continue

        filehandle.write("[Event \""+games[game]["Event"]+"\"]\n")
        for key in games[game].keys():
            if key == "moves" or key == "moves_no_comments" or key == "Event":
                continue
            filehandle.write("["+key+" \""+games[game][key]+"\"]\n")

        filehandle.write("\n" + games[game]["moves"] + "\n\n")

    filehandle.close()

if __name__ == "__main__":
    main()
