#!/usr/bin/perl

open(A, 'positions.fen');
while(<A>) {
    $s = "[Event \"Endgame Position\"]\n";
    chomp($_);
    @tmp = split(/:/, $_);
    $s .= "[White \"Player\"]\n";
    $s .= "[Black \"Opponent\"]\n";

    #Swap colors
    if ($tmp[0] =~ / b /) {
	#8/4kppp/4pn2/1K1p4/8/6P1/5r1P/3R4 w - - 2 27

	#1. swap colors
	$tmp[0] =~ tr/A-Za-z/a-zA-z/;
	$tmp[0] =~ s/B/w/;

	#2. invert and transpose
	@ttmp = split(/ /, $tmp[0]);
	@tttmp = split(/\//, $ttmp[0]);
	foreach my $tt(@tttmp) {
	    $tt = reverse($tt);
	}

	$tt = "";
	for (my $i = 0; $i < 4; $i++) {
	    $tt = $tttmp[$i];
	    $tttmp[$i] = $tttmp[@tttmp-$i-1];
	    $tttmp[@tttmp-$i-1] = $tt;
	}

	$ttmp[0] = join('/', @tttmp);
	$tmp[0] = join(' ', @ttmp);

	#3. translate move
	@ttmp = split(//, $tmp[1]);
	$tmp[1] = '';
	foreach my $tt(@ttmp) {
	    if ($tt =~ /\d/) {
		$tt *= 1;
		$tt = 9-$tt;
	    }
	    if ($tt eq 'a') {
		$tt = 'h';
	    } elsif ($tt eq 'b') {
		$tt = 'g';
	    } elsif ($tt eq 'c') {
		$tt = 'f';
	    } elsif ($tt eq 'd') {
		$tt = 'e';
	    } elsif ($tt eq 'e') {
		$tt = 'd';
	    } elsif ($tt eq 'f') {
		$tt = 'c';
	    } elsif ($tt eq 'g') {
		$tt = 'b';
	    } elsif ($tt eq 'h') {
		$tt = 'a';
	    }
	    $tmp[1] .= $tt;
	}

    }
    $s .= "[FEN \"$tmp[0]\"]\n\n";

    $s .= "1.$tmp[1] 1-0\n\n";

    print $s;
}
close(A);


exit;


open(A, 'positions.fen');
while(<A>) {
    $s = "[Event \"Endgame Position\"]\n";
    chomp($_);
    @tmp = split(/:/, $_);
    if ($tmp[2]*1 > 0) {
	$s .= "[White \"Player\"]\n";
	$s .= "[Black \"Opponent\"]\n";
    } else {
	$s .= "[White \"Opponent\"]\n";
	$s .= "[Black \"Player\"]\n";
    }
    $s .= "[FEN \"$tmp[0]\"]\n\n";

    if ($tmp[2]*1 > 0) {
	$s .= "1.$tmp[1] 1-0\n\n";
    } else {
	$s .= "1...$tmp[1] 0-1\n\n";
    }

    print $s;
}
close(A);
