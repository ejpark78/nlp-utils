#!/usr/bin/perl
#====================================================================
use strict;
use Encode;
use FileHandle;
use File::Path;
use Getopt::Long;
use Tie::LevelDB; 
#====================================================================
my (%args) = (
);

GetOptions(
	"seq|sequence=s" => \$args{"sequence"},	
	"th|threshold=f" => \$args{"threshold"},	
	"debug" => \$args{"debug"}
);
#====================================================================
# MAIN
#====================================================================
main: {
	get_hybrid_score(\%args);	
}
#====================================================================
# sub functions
#====================================================================
sub get_hybrid_score {
	binmode(STDIN, ":utf8");
	binmode(STDOUT, ":utf8");
	binmode(STDERR, ":utf8");

	my (%param) = (%{shift(@_)});

	my (%sequence) = parse_sequence($param{"sequence"});
	my $threshold = $param{"threshold"};

	my (%cnt) = ("bleu_a" => 0, "bleu_b" => 0);
	my (%sum) = ("bleu_a" => 0, "bleu_b" => 0, "only_a" => 0, "only_b" => 0);

	# bleu_a \t nc_a \t bleu_b \t nc_b
	while( my $line = <STDIN> ) {
		$line =~ s/\s+$//;

		next if( $line eq "" );
		next if( $line =~ /^#/ );

		my (@t) = split(/\t/, $line);

		my (%data) = ( 
			"bleu_a" => 0, "bleu_b" => 0,
			"nc_a" => 0, "nc_b" => 0
		);

		$data{"bleu_a"} = $t[$sequence{"bleu_a"}] if( defined($sequence{"bleu_a"}) );
		$data{"nc_a"}   = $t[$sequence{"score_a"}];

		$data{"bleu_b"} = $t[$sequence{"bleu_b"}] if( defined($sequence{"bleu_b"}) );
		# $data{"nc_b"}   = $t[$sequence{"score_b"}];

		$sum{"bleu_a"} += $data{"bleu_a"} if( defined($data{"bleu_a"}) );
		$sum{"bleu_b"} += $data{"bleu_b"} if( defined($data{"bleu_a"}) );

		# count max
		if( $data{"bleu_a"} > $data{"bleu_b"} ) {
			$sum{"max"} += $data{"bleu_a"};
			$cnt{"max_a"}++;
		} else {
			$sum{"max"} += $data{"bleu_b"};
			$cnt{"max_b"}++;
		}

		# count best
		if( $data{"nc_a"} >= $threshold ) {
			$sum{"best"} += $data{"bleu_a"};

			$cnt{"bleu_a"}++;
			$sum{"only_a"} += $data{"bleu_a"};

			printf STDERR "A\t%s\n", $line;
		} else {
			$sum{"best"} += $data{"bleu_b"};

			$cnt{"bleu_b"}++;
			$sum{"only_b"} += $data{"bleu_b"};

			printf STDERR "B\t%s\n", $line;
		}

		$cnt{"total"}++;
	}

	printf "# bleu_best: \t%.4f\t%d\t%d\n", 
		$sum{"best"}/$cnt{"total"},
		$cnt{"bleu_a"}, $cnt{"bleu_b"};

	printf "# cnt: %d, \n", $cnt{"total"};

	printf "# bleu_a: %.4f, bleu_b: %.4f, \n",
		$sum{"bleu_a"}/$cnt{"total"}, $sum{"bleu_b"}/$cnt{"total"};

	printf "# only_a: %.4f (%d), only_b: %.4f (%d), \n",
		$sum{"only_a"}/$cnt{"bleu_a"}, $cnt{"bleu_a"},
		$sum{"only_b"}/$cnt{"bleu_b"}, $cnt{"bleu_b"} 
		if( $cnt{"bleu_a"} > 0 && $cnt{"bleu_b"} );

	printf "# threshold: %.2f\n", $threshold;
	printf "# max bleu: %.4f, cnt: (%d, %d)\n", $sum{"max"}/$cnt{"total"}, $cnt{"max_a"}, $cnt{"max_b"};
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
#====================================================================
__END__

cut -f2,3,5 smt-genie.n3.ngram.txt.a > a
cut -f2,3,5 smt-genie.n3.ngram.txt.b > b

merge_file.pl a b | ../get_hybrid_score.pl -th 0.74 > best.smt-genie.n3.ngram.txt

