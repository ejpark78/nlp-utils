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
);
#====================================================================
# MAIN
#====================================================================
main: {
	my (%uniq) = ();
	my (%info) = ();

	while( <STDIN> ) {
		my (@t) = split(/\s+/, $_);

		$info{"cnt"}++;		
		$info{"word"} += scalar(@t);
		foreach( @t ) {
			$uniq{$_}++;
		}
	}

	printf "cnt\tsent word\tword\tuniq word\t%d\t%0.1f\t%d\t%d\n", 
			$info{"cnt"}, $info{"word"}/$info{"cnt"}, $info{"word"}, scalar(keys %uniq);
}
#====================================================================
# sub functions
#====================================================================
#====================================================================
__END__

