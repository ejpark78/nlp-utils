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
	"raw" => \$args{"raw"},

	"lm_f=s" => \$args{"lm_f"},
	"lm_e=s" => \$args{"lm_e"},

	"lex=s" => \$args{"lex"},
	"phrase_prob=s" => \$args{"phrase_prob"},
	
	"debug" => \$args{"debug"}
);
#====================================================================
# MAIN
#====================================================================
main: {
	phrase_prob(\%args);	
}
#====================================================================
# sub functions
#====================================================================
sub phrase_prob {
	binmode(STDIN, ":utf8");
	binmode(STDOUT, ":utf8");
	binmode(STDERR, ":utf8");

	my (%param) = (%{shift(@_)});

	if( $param{"debug"} ) {
		foreach my $k ( keys %param ) {
			print STDERR "# param: $k => ".$param{$k}."\n";
		}
	}

	# open DB
	my (%db) = ();
	$db{"lex"} = new Tie::LevelDB::DB($param{"lex"}) if( -e $param{"lex"} );

	$db{"lm_f"} = new Tie::LevelDB::DB($param{"lm_f"}) if( -e $param{"lm_f"} );
	$db{"lm_e"} = new Tie::LevelDB::DB($param{"lm_e"}) if( -e $param{"lm_e"} );

	$db{"phrase_prob"} = new Tie::LevelDB::DB($param{"phrase_prob"}) if( -e $param{"phrase_prob"} );

	my (%ngram) = ();
	my ($f, $e, $align, @sent) = ();
	while( <STDIN> ) {
		s/\s+$//;

		# buffering phrase

		next if( $_ eq "" );

		if( $args{"raw"} ) {
			if( /SOURCE: \[.+?\] (.+)$/ ) {
				$f = $1;
				next;
			} elsif( /TRANSLATED AS: (.+)\|?$/ ) {
				$e = $1;
				next;
			} elsif( /WORD ALIGNED: (.+)\|?$/ ) {
				$align = $1;

				my (%phrase) = ("src" => $f, "trg" => $e, "align" => $align);
				push(@sent, \%phrase);
				next;			
			} elsif( $_ !~ /SOURCE\/TARGET SPANS:/ ) {
				next;
			}
		} else {
			foreach( split(/<\|\|\|>/, $_) ) {
				($f, $e, $align) = split(/\|\|\|/, $_, 3);

				$f =~ s/^\s+|\s+$//g;
				$e =~ s/^\s+|\s+$//g;
				$align =~ s/^\s+|\s+$//g;

				my (%phrase) = ("src" => $f, "trg" => $e, "align" => $align);
				push(@sent, \%phrase);
			}
		}

		$f = $e = $align = "";

		# seek phrase-table
		my (%cnt) = ("unk" => 0);
		my (%sum, %buf) = ();
		foreach( @sent ) {
			my (%phrase) = (%{$_});

			my $f = $phrase{"src"};
			my $e = $phrase{"trg"};
			my (%align) = get_align_info($phrase{"align"});

			$cnt{"unk"}++ if( $e =~ /\|UNK/i );
			$cnt{"phrase"}++;

			printf STDERR "# f = $f, e = $e, align = %s\n", $phrase{"align"} if( $args{"debug"} );

			$e =~ s/\|UNK//g;

			my (@tok_f) = split(/\s+/, $f);
			my (@tok_e) = split(/\s+/, $e);

			$cnt{"tok_f"} += scalar(@tok_f);
			$cnt{"tok_e"} += scalar(@tok_e);

			# compute word align prob.
			foreach my $i ( sort keys %align ) {
				foreach my $j ( sort keys %{$align{$i}} ) {
					my $score = $db{"lex"}->Get($tok_f[$i].":".$tok_e[$j]);
					printf STDERR "# align: $i-$j\t%s\t%s\t%f\n", $tok_f[$i], $tok_e[$j], $score if( $args{"debug"} );

					$score = 0.00000001 if( $score == 0 );

					$cnt{"align"}++;
					$sum{"align"} += log($score);
				}
			}

			# compute phrase prob.
			if( defined($db{"phrase_prob"}) ) {
				my ($score, $polymorphism) = get_phrase_prob($f, $db{"phrase_prob"}->Get($f), $e);
				if( $score == 0 ) {
					$score = 0.0001;
					$polymorphism = 1;
				}

				# type 1
				$cnt{"phrase_prob"}++;
				$sum{"phrase_prob"} += log($score);

				push(@{$buf{"phrase_prob"}}, sprintf("p($f, $e, %f)", $score));

				# type 2
				$cnt{"phrase_prob2"}++;
				$sum{"phrase_prob2"} += log($score) + log(1/$polymorphism);

				push(@{$buf{"phrase_prob2"}}, sprintf("p($f, $e, %f, %d)", $score, $polymorphism));
			} 

			# compute phrase lm score
			if( defined($db{"lm_f"}) ) {
				my $score = $db{"lm_f"}->Get($f);
				$score = -10  if( !defined($score) || $score eq "" );	

				# type 1
				$cnt{"lm_f"}++;
				$sum{"lm_f"} += $score;

				push(@{$buf{"lm_f"}}, sprintf("p($f, %f)", $score));
			}

			if( defined($db{"lm_e"}) ) {
				my $score = $db{"lm_e"}->Get($e);
				$score = -10  if( !defined($score) || $score eq "" );	

				# type 1
				$cnt{"lm_e"}++;
				$sum{"lm_e"} += $score;

				push(@{$buf{"lm_e"}}, sprintf("p($f, %f)", $score));
			}
		}

		(@sent) = ();

		foreach my $k ( qw/ phrase unk tok_f tok_e / ) {
			next if( !defined($cnt{$k}) );

			printf "%d\t", $cnt{$k};
			printf STDERR "($k:%d)\t", $cnt{$k} if( $args{"debug"} );
		}

		my $flag = 0;
		foreach my $k ( qw/ align lm_f lm_e phrase_prob / ) {
			next if( !defined($sum{$k}) );
			
			$flag = 1;

			printf "%f\t", 2**(-$sum{$k}/$cnt{$k});
			printf STDERR "($k:%f/%d)\t", $sum{$k}, $cnt{$k} if( $args{"debug"} );
		}
		printf "\n" if( $flag );

		printf STDERR "\n" if( $args{"debug"} );
	}
}
#====================================================================
sub get_align_info
{
	my $align = shift(@_);

	my (%ret) = ();

	foreach( split(/\s+/, $align) ) {
		my ($f, $e) = split(/-/, $_, 2);
		$ret{$f}{$e} = 1;
	}

	return (%ret);
}
#====================================================================
sub get_phrase_lm 
{
	my $lm = shift(@_);
	my $phrase = shift(@_);

	my (@token) = split(/\s+/, $phrase);

	# p(통하 지 않 는다) => p( 는다 | 통하 지 않 ) * p( 않 | 통하 지 ) * p( 지 | 통하 ) * p(통하)

	my $ret = 0;

	print STDERR "# $phrase\n" if( $args{"debug"} );
	for( my $i=0 ; $i<scalar(@token) ; $i++ ) {
		# my $needle = join(" ", @token[($#token-$i)..$#token]);
		my $needle = join(" ", @token[0..($#token-$i)]);

		if( !defined($lm->Get($needle)) ) {
			print STDERR "p($needle, null)\n" if( $args{"debug"} );
			next;
		}

		my $score = $lm->Get($needle);
		print STDERR "p($needle, $score)\n" if( $args{"debug"} );

		$ret += $score if( defined($score) && $score ne "" );
	}
	print STDERR "# $phrase: $ret\n\n" if( $args{"debug"} );

	return $ret;
}
#====================================================================
sub get_phrase_prob 
{
	my $k = shift(@_);
	my $phrase_v = shift(@_);
	my $phrase = shift(@_);

	$phrase_v = decode('UTF-8', $phrase_v, Encode::FB_CROAK);

	my (@token) = split(/ \|\|\| /, $phrase_v);

	printf STDERR "# $k => [$phrase] := [%s]\n", join(", ", @token) if( $args{"debug"} );

	my $probability = 0;
	foreach my $unit ( @token ) {
		my ($v, $p) = split(/\t/, $unit);

		next if( $v ne $phrase );

		$probability = $p;
		last;
	}

	my $sum = 0;
	foreach my $unit ( @token ) {
		my ($v, $p) = split(/\t/, $unit);
		$sum += $p;
	}

	printf STDERR "# $k => [$sum]\n" if( $args{"debug"} );

	return ($probability, scalar(@token));
}
#====================================================================
__END__

