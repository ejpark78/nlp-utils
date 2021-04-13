#!/usr/bin/perl -w
#====================================================================
use strict;
use utf8;
use Encode;
use Getopt::Long;

use lib "$ENV{TOOLS}";
require "base_lib.pm";
#====================================================================
my (%args) = ( 
	"th" => -18,
	"th" => -1,
);
GetOptions(
	"th=f" => \$args{"th"},
	"th_high=f" => \$args{"th_high"},
	"f=s" => \$args{"filename"}
);
#====================================================================
binmode(STDIN, ":utf8");
binmode(STDOUT, ":utf8");
binmode(STDERR, ":utf8");
#====================================================================
main: {
	# check file exists
	if( !-e $args{"filename"} ) {
		printf STDERR "file is not exists: %s\n", $args{"filename"};
		exit(0);
	}

	my $start = time();

	my $total = get_file_size($args{"filename"});

	printf STDERR "total: %s (%s)\n", comma($total), sec2str(time()-$start);

	# open file
	open(FILE, "<:gzip", $args{"filename"}) || die "can not read file\n";
	binmode(FILE, ":utf8");

	my $i = 0;

	while( my $line = <FILE> ) {
		my ($score, $bitext) = split(/\t/, $line, 2); 

		$score = sprintf("%0.1f", $score);
		if( $score >= $args{"th"} && $score <= $args{"th_high"} ) {
			print $line;
		} else {
			print STDERR $line if( $args{"debug"} );
		}

		if( $i++ % 10000 == 0 ) {
			printf STDERR "loading: %s         \r", get_progress_str($i, $total, $start);
		}
	}

	close(FILE);

	printf STDERR "\nall done: %s (%s)\n", comma($total), sec2str(time()-$start);
}
#====================================================================

__END__
