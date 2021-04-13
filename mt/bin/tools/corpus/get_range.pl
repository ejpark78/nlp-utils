#!/usr/bin/perl -w
#====================================================================
use strict;
use utf8;
use Encode;
use Getopt::Long;
#====================================================================
my (%args) = ( 
	"th" => 0.9
);
GetOptions(
	"th=f" => \$args{"th"}
);
#====================================================================
binmode(STDIN, ":utf8");
binmode(STDOUT, ":utf8");
binmode(STDERR, ":utf8");
#====================================================================
main: {
	my (%range) = ();

	my $s_id = 0;
	while( my $line=<STDIN> ) {
		my ($score, $bitext) = split(/\t/, $line, 2); 

		$range{sprintf("%d", $score)}++;

		printf STDERR "." if( ++$s_id % 10000 == 0 );
		printf STDERR "(%s)\n", comma($s_id) if( $s_id % 1000000 == 0 );
	}

	foreach my $score ( sort {$a<=>$b} keys %range ) {
		printf "%d\t%d\n", $score, $range{$score};
	}

	printf "\n";
	my $sum = 0;	
	foreach my $score ( sort {$b<=>$a} keys %range ) {
		$sum += $range{$score};
		printf "%d\t%d\n", $score, $sum;
	}

}
#====================================================================
sub comma {
	my $cnt = shift(@_);

	$cnt = sprintf("%d", $cnt);
	for ( my $i = -3; $i > -1 * length($cnt); $i -= 4 ){
	    substr( $cnt, $i, 0 ) = ',';
	}

	return $cnt;
}
#====================================================================

__END__
