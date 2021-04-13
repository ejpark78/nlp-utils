#!/usr/bin/perl -w

use strict;
use utf8;
use Getopt::Long;

use lib "$ENV{TOOLS}";
require "base_lib.pm";


my (%args) = ();

GetOptions(
	"f=s" => \$args{"filename"},
	"debug" => \$args{"debug"}
);


binmode(STDIN, ":utf8");
binmode(STDOUT, ":utf8");
binmode(STDERR, ":utf8");


main: {
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

	my (%range) = ();
	while( my $line = <FILE> ) {
		my ($score, $bitext) = split(/\t/, $line, 2); 

		$range{sprintf("%d", $score)}++;

		if( $i++ % 10000 == 0 ) {
			printf STDERR "loading: %s   \r", get_progress_str($i, $total, $start);
		}
	}
	close(FILE);

	my $sum = 0;	
	foreach my $score ( sort {$a<=>$b} keys %range ) {
		$sum += $range{$score};
		printf "%d\t%d\t%d\n", $score, $range{$score}, $sum;
	}

	printf STDERR "\nall done: %s (%s)\n", comma($total), sec2str(time()-$start);
}


__END__

