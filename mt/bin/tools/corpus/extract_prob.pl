#!/usr/bin/perl -w
#====================================================================
use strict;
use utf8;
use Encode;
use Getopt::Long;
use BerkeleyDB; 
use Math::BigFloat;
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

	my $buf = "";
	while( my $line = <STDIN> ) {
		$line =~ s/\s+$//;
		
		next if( $line !~ /^# Sentence pair/ );
		
		# # Sentence pair (1) source length 7 target length 6 alignment score : 3.0147e-08
		# But don 't you see ? 
		# NULL ({ }) ¿ ({ }) Pero ({ 1 }) no ({ 2 3 }) ves ({ 4 5 }) ? ({ 6 }) El ({ }) Sr. ({ }) 

		# ==> source \t target \t score

		my ($tag, $score) = split(/:/, $line, 2);

		$score =~ s/^\s+|\s+$//g;

		printf "%s\n", $score;

		$s_id++;

		printf STDERR "." if( $s_id % 10000 == 0 );
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

