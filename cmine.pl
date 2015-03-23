#!/usr/bin/perl

use IPC::Open3;

my $depth = 25;
my $hash = 512;
my $pv = 3;
my $syzygypath = "syzygy";
my $threads = 8;
my $threshold = 100;

if (@ARGV != 1) {
    print "USAGE: perl stockfish_mine.pl <file_to_parse>.fen\n";
    exit;
}
my $file = $ARGV[0];

my $pid = open3(\*SF_IN, \*SF_OUT, \*SF_ERR, './stockfish-6-64') or die "open3 failed $!";
open(FEN_LIST, $file);

print SF_IN "setoption name hash value $hash\n";
print SF_IN "setoption name multipv value $pv\n";
print SF_IN "setoption name syzygypath value $syzygypath\n";
print SF_IN "setoption name threads value $threads\n";

while ($fen = <FEN_LIST>) {
    next if !isValidFen($fen);

    #print $fen;
    print SF_IN "position fen $fen";
    print SF_IN "go depth $depth\n";

    @tmp = ();
    while (<SF_OUT>) {
	last if $_ =~ /bestmove/;

	if ($_ =~ /info depth $depth/) {
	    $_ =~ /multipv (\d+) score cp (-*\d+) nodes .*?pv ([A-Za-z0-9]+)/;
	    #print $_;
	    #print "setting $1 to $2\n";
	    $tmp[$1][0] = $2;
	    $tmp[$1][1] = $3;
	}
    }

    #print "1st pv eval is: $tmp[1][0]\n";
    #print "3rd pv eval is: $tmp[$pv][0]\n";

    #There are only one or two winning moves.
    if (abs($tmp[$pv][0]) < $threshold && abs($tmp[1][0]) > $threshold) {
	#print $fen;
	#print "Winning move is $tmp[1][0]\n";
	$fen =~ s/[\r\n]+\Z//;
	print "$fen:$tmp[1][1]:$tmp[1][0]\n";
    #} else {
	#print "No good: 3 is $tmp[$pv][0] and 1 is $tmp[1][0]\n";
    }
}

close(FEN_LIST);
close($sf);

sub isValidFen() {
    $_[0] =~ /(.*?) .*?$/;
    $tfen = $1;

    #Queens are off so we have an endgame
    if ($tfen !~ /Q/ && $tfen !~ /q/) {
	return 1;
    } else {
	return 0;
    }
}
