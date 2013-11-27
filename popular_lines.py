#!/usr/bin/python

import datrie
import re
import string
import sys

max_move = 20
game_tree = datrie.Trie(string.printable)
game_text = []
game_text_index = 0
result_regex = re.compile("[0-9]-")
black = 1
white = 0
color = white

def main():
	global black
	global color
	global game_text
	global game_text_index
	global white
	line = ""
	r = 0
	bracket_str = re.compile("\[")
	event_str = re.compile("\[Event ")
	space = re.compile("^ +$")

	if (len(sys.argv) != 2 and len(sys.argv) != 3):
		print "USAGE: popular_lines <input file> [white|black]\n\nExample: popular_lines test.pgn white\n"
		sys.exit(0)

	file = sys.argv[1]
	if (len(sys.argv) == 3 and (sys.argv[2].lower() == "black")):
		color = black

	fh = open(file, 'r')
	for row in fh.readlines():
		row = row.rstrip('\n')
		if (event_str.match(row)):
			# don't process on line 1
			if (r == 1):
				process_line(line)
				game_text_index += 1
				line = ""
			r = 1

		if (len(game_text) < game_text_index):
			print "game_text_index is growing too quickly. it is " + str(game_text_index) + " and the game_text is only " + str(len(game_text))
			sys.exit(1)
		elif (len(game_text) < game_text_index+1):
			game_text.append(row+"\n")
		else:
			game_text[game_text_index] += row + "\n"

		if ((not bracket_str.match(row)) and (not space.match(row))
				and (len(row) > 0)):
			# if the line does not end with a space (required between moves) and also 
			# does not end with a dot (a move already began), add a space
			if (row[-1] != " " and row[-1] != "."):
				row += " "
			line += row

	#final one doesn't trigger by seeing a new game
	process_line(line)

	fh.close()

#	drop_branch('1.e4 c6 2.d4 d5 3.e5 ')

	for g in game_text:
		if (g != ""):
			print g

#trie[u'1.e4 c6'] = [10,11]
#trie[u'1.e4 c6 2.d4 d6'] = [45,46]
#
#print trie.keys(u'1.e4') 
#print trie.items(u'1.e4')
#print trie.values(u'1.e4')
#[u'1.e4 c6', u'1.e4 c6 2.d4 d6']
#[(u'1.e4 c6', [10, 11]), (u'1.e4 c6 2.d4 d6', [45, 46])]
#[[10, 11], [45, 46]]
def process_line(line):
	i = 0
	global result_regex
	# TODO: strip line after max_move ?
	m = re.split("\d+\. *", line)
	bw = []
	t = ""
	t_arr = []
	for v in m:
		if (i == 0):
			i += 1
			continue

		bw = v.split(" ")
		if (color == black):
			t_arr.append(str(i))
			t_arr.append(".")
			t_arr.append(bw[0])
			t_arr.append(' ')
			t = ''.join(t_arr)

		if (color == black and len(bw) > 1):
			if (result_regex.match(bw[1])):
				return
			next_move = bw[1]
		elif (color == white):
			next_move = bw[0]
			print "WHITE NOT IMPLEMENTED YET."
			sys.exit(1)
		else:
			# this should never happen
			print "Color is black and length of the move array is 0."
			sys.exit(1)
			return

		# add white move
		ut = unicode(t)

		try:
			# try to extend the existing move array
			index_dict = game_tree[ut]
			try:
				index_dict[next_move].extend([game_text_index])
			except:
				#tree up until now exists, but this is a new next move
				index_dict[next_move] = [game_text_index]
			game_tree[ut] = index_dict
		except:
			game_tree[ut] = {next_move: [game_text_index]}

		# add black move
		if (len(bw) > 1):
			t_arr.append(bw[1])
			t_arr.append(' ')
			t = ''.join(t_arr)

		i += 1

def drop_branch(branch):
	keys = game_tree.keys(unicode(branch))

	for key in keys:
		game_indices = game_tree[key].values()
		for fake_index in game_indices:
			for index in fake_index:
				game_text[index] = ""

if __name__ == "__main__":
	main()
