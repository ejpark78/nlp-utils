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
	my $s_id = 0;
	while( my $line=<STDIN> ) {
		my ($score, $bitext) = split(/\t/, $line, 2); 

		$score = sprintf("%d", $score);
		print $bitext if( $score == $args{"th"} );

		printf STDERR "." if( ++$s_id % 10000 == 0 );
		printf STDERR "(%s)\n", comma($s_id) if( $s_id % 1000000 == 0 );
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
