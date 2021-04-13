#!/usr/bin/perl -w
#====================================================================
use strict;
use utf8;
use Encode;
use Getopt::Long;
use TryCatch;

use lib "$ENV{TOOLS}";
require "base_lib.pm";
#====================================================================
my (%args) = ( 
	"f2e" => 0,
	"e2f" => 0,
);
GetOptions(
	"debug" => \$args{"debug"},
	"f2e=f" => \$args{"f2e"},
	"e2f=f" => \$args{"e2f"},
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
		$line =~ s/\s+$//;
		
		my ($giza_f2e, $giza_e2f, $f, $e) = split(/\t/, $line, 4);

		my (@token_f) = split(/\s+/, $f);
		my (@token_e) = split(/\s+/, $e);

		try {
			my $score = -100;
			if( $giza_f2e > $args{"f2e"} && $giza_e2f > $args{"e2f"} ) {
				$score = (log($giza_f2e) / scalar(@token_f)) + (log($giza_e2f) / scalar(@token_e));
			}

			if( $score != -100 ) {
				printf "%f\t%s\t%s\n", $score, $f, $e;
			} else {
				printf STDERR "\n# giza score (%f, %f, %f): %s\n", $score, $giza_f2e, $giza_e2f, $line if( $args{"debug"} );
			}
		} catch($err) {
			printf STDERR "\n# giza score (%f, %f): %s\n", $giza_f2e, $giza_e2f, $line if( $args{"debug"} );
		}

		if( $i++ % 10000 == 0 ) {
			printf STDERR "loading: %s        \r", get_progress_str($i, $total, $start);
		}
	}

	close(FILE);

	printf STDERR "\nall done: %s (%s)\n", comma($total), sec2str(time()-$start);
}
#====================================================================
__END__      

