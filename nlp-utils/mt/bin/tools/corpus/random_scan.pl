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
	binmode(STDIN, ":utf8");
	binmode(STDOUT, ":utf8");
	binmode(STDERR, ":utf8");

	my $cnt = 0;
	while( my $line=<STDIN> ) {

		next if( $cnt-- != 0 );
		$cnt = int(rand(10000));

	    print $line;
	}
}
#====================================================================
# sub functions
#====================================================================
sub comma {
	my $cnt = shift(@_);

	$cnt = reverse join ",", (reverse $cnt) =~ /(\d{1,3})/g;

	return $cnt;
}
#====================================================================
__END__


