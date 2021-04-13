#!/usr/bin/perl -w
#====================================================================
use strict;
use utf8;
use Getopt::Long;
#====================================================================
my (%args) = (
);

GetOptions(
);
#====================================================================
binmode(STDIN, ":utf8");
binmode(STDOUT, ":utf8");
#====================================================================
main: {
	my ($sum, $cnt) = (0, 0);
	while( my $line = <STDIN> ) {
		$line =~ s/\s+$//;
		
		next if( $line !~ /Translation took/ );

		my (@t) = split(/\s+/, $line);
		
		next if( $t[4] !~ /\d/ );
		# next if( $t[4] =~ /\w/i );

		# print STDERR $line."\n".$t[4]."\n";

		$cnt++;
		$sum += $t[4];
	}

	# printf "%d %d", $sum, $cnt;
	printf "%.2f %d %d", $sum/$cnt, $sum, $cnt;
}
#====================================================================
__END__