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
	get_svm_rate(\%args);	
}
#====================================================================
# sub functions
#====================================================================
sub get_svm_rate {
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

	my (%info, @data) = ();
	while( my $line = <STDIN> ) {
		$line =~ s/\s+$//;

		next if( $line eq "" );

		my (@t) = split(/\t/, $line);

		my $class = $t[$seq{"class"}];
		my $predict = $t[$seq{"predict"}];

		$class = 1 if( $class eq "smt" );
		$class = 0 if( $class eq "lbmt" );

		# ko,lbmt,lbmt_score,smt,smt_score
		my $ko   = $t[$seq{"ko"}];
		my $ref  = $t[$seq{"ref"}];
		my $smt  = $t[$seq{"smt"}];
		my $lbmt = $t[$seq{"lbmt"}];
		my $smt_score  = $t[$seq{"smt_score"}];
		my $lbmt_score = $t[$seq{"lbmt_score"}];
		my ($tst, $score) = ();

		if( $predict == 1 ) {
			$tst = $smt;
			$score = $smt_score;
		} else {
			$tst = $lbmt;
			$score = $lbmt_score;
		}

		push(@data, sprintf("%s\t%s\t%s", $ko, $tst, $ref));

		$info{"hybrid"} += $score;

		$info{"T"}++ if( $class == 1 );
		$info{"F"}++ if( $class == 0 );
		$info{"P"}++ if( $predict == 1 );
		$info{"N"}++ if( $predict == 0 );

		$info{"TP"}++ if( $class == 1 && $predict == 1 );
		$info{"FN"}++ if( $class == 1 && $predict == 0 );
		$info{"FP"}++ if( $class == 0 && $predict == 1 );
		$info{"TN"}++ if( $class == 0 && $predict == 0 );

		$info{"ACC_TP"}++ if( $smt_score == $lbmt_score || $class == 1 && $predict == 1 );
		$info{"*"}++ if( $smt_score == $lbmt_score );
	}

	foreach my $line ( @data ) {
		printf "hybrid_auto_eval_data\t%s\n", $line;
	}

	printf "\n";

	my $precision = ($info{"TP"} + $info{"FP"} > 0) ? $info{"TP"} / ($info{"TP"} + $info{"FP"}) : 0;
	my $recall = ($info{"TP"} + $info{"FN"} > 0) ? $info{"TP"} / ($info{"TP"} + $info{"FN"}) : 0;
	my $f = ($precision + $recall > 0) ? 2 * ($precision * $recall) / ($precision + $recall) : 0;
	my $acc = ($info{"P"} + $info{"N"} > 0) ? ($info{"ACC_TP"} + $info{"TN"}) / ($info{"P"} + $info{"N"}) : 0;

	printf STDERR "acc:$acc ($info{ACC_TP} + $info{TN}) \n";

	# printf "T\tF\tP\tN\tTP\tTN\tFP\tFN\tPrecision\tRecall\tF-measure\n",
	printf "performance\t%f\t%f\t%f\t%f\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n\n",
		$precision, 
		$recall, 
		$f,
		$acc,
		$info{"T"}, $info{"F"}, $info{"P"}, $info{"N"}, 
		$info{"TP"}, $info{"TN"}, $info{"FP"}, $info{"FN"},
		$info{"*"};

	printf "hybrid_score\t%f\n\n", $info{"hybrid"} / ($info{"P"} + $info{"N"}) / 4;


	# printf "T: %d, F: %d, P: %d, N: %d, TP: %d, TN: %d, FP: %d, FN: %d, Precision: %f, Recall: %f, F-measure: %f\n",
	# 	$info{"T"}, $info{"F"}, $info{"P"}, $info{"N"}, 
	# 	$info{"TP"}, $info{"TN"}, $info{"FP"}, $info{"FN"}, 
	# 	$precision, 
	# 	$recall, 
	# 	$f;

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

