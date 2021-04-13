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
my (%args) = (
	"fields" => "1",
);

GetOptions(
	# "n=i" => \$args{"n"},
	"f|fields=i" => \$args{"fields"},

	"lm=s" => \$args{"lm"},
	"backoff|lm_backoff=s" => \$args{"lm_backoff"},

	"debug" => \$args{"debug"}
);
#====================================================================
# MAIN
#====================================================================
main: {
	lm_score(\%args);	
}
#====================================================================
# sub functions
#====================================================================
sub lm_score {
	binmode(STDIN, ":utf8");
	binmode(STDOUT, ":utf8");
	binmode(STDERR, ":utf8");

	my (%param) = (%{shift(@_)});
	$param{"fields"}--;

	if( $param{"debug"} ) {
		foreach my $k ( keys %param ) {
			print STDERR "# param: $k => ".$param{$k}."\n";
		}
	}

	# open DB
	my (%ngram_db) = ();

	$ngram_db{"lm"} = new Tie::LevelDB::DB($param{"lm"}) if( -e $param{"lm"} );
	$ngram_db{"lm_backoff"} = new Tie::LevelDB::DB($param{"lm_backoff"}) if( -e $param{"lm_backoff"} );

	my (%ngram) = ();
	while( my $line = <STDIN> ) {
		$line =~ s/\s+$//;

		# print STDERR "# $line:".$db->Get($line)."\n" if( defined($db->Get($line)) );

		next if( $line eq "" );
		# if( $line =~ /^#/ ) {
		# 	print "$line\n";
		# 	print STDERR "$line\n";
		# 	next;
		# }

		my (@t) = split(/\t/, $line);
		my (@token) = split(/\s+/, $t[$param{"fields"}]);

		printf STDERR "\n######################\n# input str: %s\n", $t[$param{"fields"}] if( $param{"debug"} );

		my (%ngram, %lm_score, %buf_log) = ();

		get_lm_candidate(\@token, 1, \@{$ngram{"n1"}});
		($lm_score{"n1"}, $buf_log{"n1"}) = get_lm_score(\%ngram_db, 1, \@{$ngram{"n1"}});

		get_lm_candidate(\@token, 2, \@{$ngram{"n2"}});
		($lm_score{"n2"}, $buf_log{"n2"}) = get_lm_score(\%ngram_db, 2, \@{$ngram{"n2"}});

		get_lm_candidate(\@token, 3, \@{$ngram{"n3"}});
		($lm_score{"n3"}, $buf_log{"n3"}) = get_lm_score(\%ngram_db, 3, \@{$ngram{"n3"}});

		get_lm_candidate(\@token, 4, \@{$ngram{"n4"}});
		($lm_score{"n4"}, $buf_log{"n4"}) = get_lm_score(\%ngram_db, 4, \@{$ngram{"n4"}});

		get_lm_candidate(\@token, 5, \@{$ngram{"n5"}});
		($lm_score{"n5"}, $buf_log{"n5"}) = get_lm_score(\%ngram_db, 5, \@{$ngram{"n5"}});

		foreach( sort keys %lm_score ) {
			my $log = "";
			$log = join(", ", @{$buf_log{$_}}) if( defined($buf_log{$_}) );

			printf "%s\t%.4f\t%.4f\t%s\t", 
				$_,
				$lm_score{$_}, 
				2**(-$lm_score{$_}), 
				$log;
		}
		printf "%s\n", $line;

		# printf "%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%s\n", 
		# 	$lm_score{"n1"}, $lm_score{"n2"}, $lm_score{"n3"}, $lm_score{"n4"}, $lm_score{"n5"},
		# 	$line;
	}
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

