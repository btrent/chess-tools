chess-tools
===========

The purpose of this repo is to host a collection of tools related to chess. At the moment it contains:

Popular Lines
-----------
Popular Lines is a script to strip all but the most popular opening lines from a collection of games stored in a PGN-formatted file.

This is useful for studying opening theory. Suggested use:
* Get access to a games database. There are many great free sources on the Internet, including TWIC and most of the FICS collection from the past 10 years. A DB size of 3 million games or more is a good starting point.
* Filter games from the database using something like SCID, grabbing games from an opening of your choice. For example, to do the Caro Kann you'd search for ECO codes B10-B19. You may also want to filter by result (maybe only games where one color wins), rating of players, etc.
* Save that filter as a PGN.
* Run this magic script!
* The script generates a PGN file that contains only games that have the most often played lines.

You can now use this PGN file to study openings, for example by importing back into SCID and loading random games.

Merge Duplicate Games
-----------
This script will parse a PGN file and merge duplicate games into a single record.
Output is a PGN file named <original_filename>_clean.pgn.

Sort By Year
-----------
This script will parse a PGN file and sort all games into new PGN files named according to the year of the game (1888.pgn, 2012.pgn, etc.).


