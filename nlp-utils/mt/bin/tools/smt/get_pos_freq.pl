#!/usr/bin/perl
#====================================================================
use strict;
use Encode;
use FileHandle;
use File::Path;
use Getopt::Long;
use Tie::LevelDB; 
use POSIX;
#====================================================================
my (%args) = ();

GetOptions(
	"seq|sequence=s" => \$args{"sequence"},

	"debug" => \$args{"debug"}
);
#====================================================================
# MAIN
#====================================================================
main: {
	get_features(\%args);	
}
#====================================================================
# sub functions
#====================================================================
sub get_features {
	binmode(STDIN, ":utf8");
	binmode(STDOUT, ":utf8");
	binmode(STDERR, ":utf8");

	my (%param) = (%{shift(@_)});
	my (%seq) = parse_sequence($param{"sequence"});

	if( $param{"debug"} ) {
		foreach my $k ( keys %param ) {
			print STDERR "# param: $k => ".$param{$k}."\n";
		}
	}

	while( my $line = <STDIN> ) {
		$line =~ s/\s+$//;

		next if( $line eq "" );

		my (@t) = split(/\t/, $line);		
		get_pos_features($t[$seq{"pos"}]);
	}
}
#====================================================================
sub get_pos_features {
	my $text = shift(@_);

	my (@token_pos) = split(/\s+/, $text);

	my (%pos_count) = ("V" => 0, "E" => 0, "N" => 0, "J" => 0, "X" => 0, "M" => 0);
	foreach my $word ( @token_pos ) {
		my ($w, $p) = split(/\//, $word, 2);
		$p =~ s/^(.).+$/$1/g;
		$pos_count{$p}++;

		printf STDERR "# pos: $w:$p\n" if( $param{"debug"} );
	}

	printf STDERR "# pos: %s\n", $t[$seq{"pos"}] if( $param{"debug"} );

	printf "%d\t%d\t%d\t%d\t%s\n", 
		$pos_count{"V"},
		$pos_count{"J"},
		$pos_count{"N"}, 
		$pos_count{"E"}, 
		$line;
}
#====================================================================
sub parse_sequence {
	my $sequence = shift(@_);

	my $idx = 0;
	my (%input_sequence) = ();
	foreach my $pos ( split(/,/, $sequence) ) {
		$input_sequence{$pos} = $idx;
		$idx++;
	}

	return (%input_sequence);
}
#====================================================================
sub get_hash_str
{
	my (%data) = %{shift(@_)};

	my (@buf) = ();
	foreach my $k ( sort keys %data ) {
		push(@buf, "$k=>".sprintf("%.2f", $data{$k}));
	}

	return join(", \n# - ", @buf);
}
#====================================================================
sub get_hash_str_2key
{
	my (%data) = %{shift(@_)};

	my (@buf) = ();
	foreach my $k ( sort keys %data ) {
		foreach my $kk ( sort keys %{$data{$k}} ) {
			push(@buf, "$k=>$kk=>".sprintf("%.2f", $data{$k}{$kk}));
		}
	}

	return join(", \n# - ", @buf);
}
#====================================================================
sub get_lm_score
{
	my (%lm_db) = %{shift(@_)};
	my $n = shift(@_);
	my (@lm_candidate) = @{shift(@_)};

	my $nosmoothing = 0;
	# $nosmoothing = 1;

	my ($lm_score) = (0);
	my (%ret) = ();

	foreach my $np_pos ( @lm_candidate ) {
		# without pos tag
		my $np = $np_pos;
		$np =~ s/\/[A-Z]+?/ /g;

		next if( !defined($lm_db{"lm"}) );

		if( defined($lm_db{"lm"}->Get($np)) ) {
			my $score = $lm_db{"lm"}->Get($np);

			$lm_score += $score;
			$ret{$np} += $score;
			next;
		} 

		# ignore smoothing
		if( $nosmoothing ) {
			my $score = log(1/10000000000);
			$lm_score += $score;
			$ret{$np} += $score;
			# printf ">>>>$np:>%.f\n", log(1/10000000000);
			next;
		}

		# backoff - KneserNey
		my $score_backoff = get_backoff(\%lm_db, $np);

		$ret{$np} += $score_backoff;
		$lm_score += $score_backoff;
	}

	my (@buf) = ();
	foreach my $k ( sort keys %ret ) { 
		push(@buf, "p($k, $ret{$k})");
	}

	my $ret_score = $lm_score;
	$ret_score = $lm_score / scalar(@buf) if( scalar(@buf) > 0 );

	if( $args{"debug"} ) {
		print STDERR "\n# summary\n";

		print STDERR "# p(".join(" | ", @lm_candidate).") ~= \n";
		print STDERR "# ".join("\n# + ", @buf);
		print STDERR "\n# ~= perplexity= ".(2**(-$ret_score)).", log(p)=$ret_score, ($lm_score / ".scalar(@buf).")";
		print STDERR ", ".POSIX::pow(2, $lm_score)."\n\n";
	}

	# return POSIX::pow(2, $lm_score);
	return ($ret_score, \@buf);
}
#====================================================================
sub get_backoff
{
	my (%lm_db) = (%{shift(@_)});
	my $np = shift(@_);

	print STDERR "\n# get_backoff\n" if( $args{"debug"} );

	my $score_backoff = 0;
	my (@backoff_log) = ();

	my $needle = $np;
	$needle =~ s/^[ ]+ //;

	# $ret{$needle} += 0;
	if( defined($lm_db{"lm"}->Get($needle)) ) {
		my $score = $lm_db{"lm"}->Get($needle);

		$score_backoff += $score;
		push(@backoff_log, "p($needle, $score)");

		printf STDERR "# \t%s\n", join("+", @backoff_log) if( $args{"debug"} );

		return $score_backoff;
	}

	# p(a b c) = p(c) + b(b) + b(a b)
	# p(d | a b c) = p(d) + b(c) + b(b c) + b(a b c)
	# b( so | i love you) = p(so) + b(you) + b(love you) + b(i love you)

	return $score_backoff if( !defined($lm_db{"lm_backoff"}) );

	my (@token_np) = split(/ /, $np);
	$needle = pop(@token_np);

	if( $needle ne "</s>" ) {
		if( defined($lm_db{"lm"}->Get($needle)) ) {
			my $score = $lm_db{"lm"}->Get($needle);

			$score_backoff += $score;
			push(@backoff_log, "p($needle, $score)");
		} else {
			push(@backoff_log, "p($needle, null)");			
		}
	}

	for( my $i=0 ; $i<scalar(@token_np) ; $i++ ) {
		$needle = join(" ", @token_np[($#token_np-$i)..$#token_np]);

		next if( $needle eq "<s>" || $needle eq "</s>" );

		if( !defined($lm_db{"lm_backoff"}->Get($needle)) ) {
			push(@backoff_log, "b($needle, null)");			
			next;
		}

		my $score = $lm_db{"lm_backoff"}->Get($needle);
		
		$score_backoff += $score;			
		push(@backoff_log, "b($needle, $score)");			
	}

	printf STDERR "# \tp(%s) := %f, %s\n", $np, $score_backoff, join(" + ", @backoff_log) if( $args{"debug"} );

	# return $score_backoff/scalar(@backoff_log);
	return $score_backoff;
}
#====================================================================
sub get_lm_candidate
{
	my (@token) = (@{shift(@_)});
	my $n = shift(@_);
	my $ret = shift(@_);

	$n--;

	# <s> he have the car </s>

	for( my $i=0 ; $i<scalar($n) ; $i++ ) {
		unshift(@token, "<s>");
		push(@token, "</s>");
	}

	my (%count) = ("total" => 0, "v" => 0, "token_v" => 0);
	foreach my $w ( @token ) {
		$count{"token_v"} ++ if( $w =~ /\/V/i );
	}

	for( my $i=0 ; $i<scalar(@token)-$n ; $i++ ) {
		my $buf = join(" ", @token[$i..($i+$n)]);

		$buf =~ s/\s+$//;
		$buf =~ s/^(<s> )+/<s> /;
		$buf =~ s/( <\/s>)+$/ <\/s>/;

		next if( $buf eq "" );

		push(@{$ret}, $buf);

		$count{"total"}++;
		$count{"v"}++ if( $buf =~ /\/V/i );
	}

	if( $args{"debug"} ) {
		print STDERR "\n";
		print STDERR "### get_lm_candidate: n=$n\n";
		print STDERR "# input token (n: $n): ".join(" ", @token)."\n";
		print STDERR "# ngram list: (".scalar(@{$ret}).") ".join(" ||| ", @{$ret})."\n";
	}

	$count{"token"} = scalar(@token);
	$count{"total"} = -1 if( $count{"total"} == 0 );

	return (%count);
}
#====================================================================
sub get_str_ngram
{
	my (@token) = (@{shift(@_)});
	my $n = shift(@_);
	my $ret = shift(@_);

	$n--;

	for( my $i=0 ; $i<scalar($n) ; $i++ ) {
		unshift(@token, "<s>");
		push(@token, "</s>");
	}

	my (%count) = ("total" => 0, "v" => 0, "token_v" => 0);
	foreach my $w ( @token ) {
		$count{"token_v"} ++ if( $w =~ /\/V/i );
	}

	for( my $i=0 ; $i<scalar(@token)-$n ; $i++ ) {
		my $buf = join(" ", @token[$i..$i+$n]);

		$buf =~ s/\s+$//;

		next if( $buf eq "" );

		$ret->{$buf} = 1;

		$count{"total"}++;
		$count{"v"}++ if( $buf =~ /\/V/i );
	}

	if( $args{"debug"} ) {
		print STDERR "\n";
		print STDERR "### get_str_ngram: n=$n\n";
		print STDERR "# input token (n: $n): ".join(" ", @token)."\n";
		print STDERR "# ngram list: (".scalar(keys %{$ret}).") ".join(" ||| ", keys %{$ret})."\n";
	}

	$count{"token"} = scalar(@token);
	$count{"total"} = -1 if( $count{"total"} == 0 );

	return (%count);
}
#====================================================================
__END__

