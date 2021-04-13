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
);

GetOptions(
	"seq|sequence=s" => \$args{"sequence"},

	"db|lex=s" => \$args{"db"},

	"debug" => \$args{"debug"}
);
#====================================================================
# MAIN
#====================================================================
main: {
	lex_prob(\%args);	
}
#====================================================================
# sub functions
#====================================================================
sub lex_prob {
	binmode(STDIN, ":utf8");
	binmode(STDOUT, ":utf8");
	binmode(STDERR, ":utf8");

	my (%param) = (%{shift(@_)});
	my (%seq) = parse_sequence($param{"sequence"});

	$seq{"ref"} = $seq{"src"} if( !defined($seq{"ref"}) );

	if( $param{"debug"} ) {
		foreach my $k ( keys %param ) {
			print STDERR "# param: $k => ".$param{$k}."\n";
		}
	}

	# get sequence
	print STDERR "# Opening: ".$param{"db"}."\n" if( -e $param{"db"} );

	# open DB
	my ($lex_db) = ();
	$lex_db = new Tie::LevelDB::DB($param{"db"}) if( -e $param{"db"} );

	my (%ngram_f, %ngram_e) = ();
	while( my $line = <STDIN> ) {
		$line =~ s/\s+$//;

		next if( $line eq "" );
		# if( $line =~ /^#/ ) {
		# 	print "$line\n";
		# 	print STDERR "$line\n";
		# 	next;
		# }

		my (@t) = split(/\t/, $line);
		my (@token_src) = split(/\s+/, $t[$seq{"src"}]);
		my (@token_tst) = split(/\s+/, $t[$seq{"tst"}]);
		my (@token_ref) = split(/\s+/, $t[$seq{"ref"}]);

		my (%ngram_src, %ngram_tst, %ngram_ref) = ();
		get_ngram(\@token_src, 1, \@{$ngram_src{"n1"}});
		get_ngram(\@token_tst, 1, \@{$ngram_tst{"n1"}});
		get_ngram(\@token_ref, 1, \@{$ngram_ref{"n1"}});

		my (%tst, %ref) = ();
		foreach my $f ( @{$ngram_src{"n1"}} ) {
			get_align_prob($f, $lex_db, \@{$ngram_tst{"n1"}}, \%tst);
			get_align_prob($f, $lex_db, \@{$ngram_ref{"n1"}}, \%ref);
		}

		$tst{"perplexity"} = $ref{"perplexity"} = 0;
		$tst{"perplexity"} = 2**(-$tst{"sum"}/$tst{"cnt"}) if( $tst{"cnt"} > 0 );
		$ref{"perplexity"} = 2**(-$ref{"sum"}/$ref{"cnt"}) if( $ref{"cnt"} > 0 );

		printf "%f\t%f\t%f\t%s\n", 
			$tst{"perplexity"}, 
			$ref{"perplexity"}, 
			($ref{"perplexity"} - $tst{"perplexity"}),
			$line;

		printf STDERR "\n" if( $args{"debug"} );
	}
}
#====================================================================
sub get_align_prob
{
	my $f = shift(@_);
	my $lex_db = shift(@_);
	my (@ngram) = (@{shift(@_)});
	my $sent_prob = shift(@_);

	my (%prob, %dict) = ();
	foreach my $e ( @ngram ) {
		my $k = "$f:$e";
		if( defined($lex_db->Get($k)) && $prob{$f} < $lex_db->Get($k) ) {
			$dict{$f} = $k;
			$prob{$f} = $lex_db->Get($k);
		}
	}

	foreach my $f ( keys %prob ) {
		$sent_prob->{"cnt"}++;
		$sent_prob->{"sum"} += log($prob{$f});
		print STDERR "# $f ($dict{$f}) := $prob{$f}\n" if( $args{"debug"} );
	}
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

	my $ret_score = $lm_score / scalar(@buf);

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
sub get_ngram
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
		print STDERR "### get_ngram: n=$n\n";
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

