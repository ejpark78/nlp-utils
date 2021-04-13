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

	"debug" => \$args{"debug"}
);
#====================================================================
# MAIN
#====================================================================
main: {
	get_feature_diff_main(\%args);	
}
#====================================================================
# sub functions
#====================================================================
sub get_feature_diff_main {
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

	my (%ngram_f, %ngram_e) = ();
	while( my $line = <STDIN> ) {
		$line =~ s/\s+$//;

		next if( $line eq "" );
		# src,tst1,tst2,
		# lm_f1,lm_f2,lm_f3,lm_f4,lm_f5,
		# smt_lm_e1,smt_lm_e2,smt_lm_e3,smt_lm_e4,smt_lm_e5,
		# lbmt_lm_e1,lbmt_lm_e2,lbmt_lm_e3,lbmt_lm_e4,lbmt_lm_e5

		my (@t) = split(/\t/, $line);

		my (@token_src) = split(/\s+/, $t[$seq{"src"}]);
		my (@token_tst1) = split(/\s+/, $t[$seq{"tst1"}]);
		my (@token_tst2) = split(/\s+/, $t[$seq{"tst2"}]);

		my (%lm_diff) = ();
		for( my $i=1 ; $i<=5 ; $i++ ) {
			push(@{$lm_diff{"tst1"}}, ($t[$seq{"lm_f$i"}] - $t[$seq{"smt_lm_e$i"}]));
			push(@{$lm_diff{"tst2"}}, ($t[$seq{"lm_f$i"}] - $t[$seq{"lbmt_lm_e$i"}]));
			push(@{$lm_diff{"tst1&2"}}, ($t[$seq{"smt_lm_e$i"}] - $t[$seq{"lbmt_lm_e$i"}]));
		}

		my (%len) = ();
		$len{"tst1_tst2"} = scalar(@token_tst1) - scalar(@token_tst2);

		$len{"tst1"} = scalar(@token_src) - scalar(@token_tst1);
		$len{"tst1_rate"} = ( $len{"tst1"} > 0 ) ? scalar(@token_tst1) / $len{"tst1"} : 0;

		$len{"tst2"} = scalar(@token_src) - scalar(@token_tst2);
		$len{"tst2_rate"} = ( $len{"tst2"} > 0 ) ? scalar(@token_tst2) / $len{"tst2"} : 0;

		printf "%d\t%d\t%d\t%f\t%d\t%f\t%s\t%s\t%s\t%d\n", 
			scalar(@token_tst1),
			scalar(@token_tst2),
			$len{"tst1"},
			$len{"tst1_rate"},
			$len{"tst2"},
			$len{"tst2_rate"},
			join("\t", @{$lm_diff{"tst1"}}),
			join("\t", @{$lm_diff{"tst2"}}),
			join("\t", @{$lm_diff{"tst1&2"}}),
			$len{"tst1_tst2"},
			;

		printf STDERR "\n" if( $args{"debug"} );
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
__END__

