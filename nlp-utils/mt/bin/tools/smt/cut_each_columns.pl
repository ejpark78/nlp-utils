#!/usr/bin/perl -w

use utf8;
use strict;
use Getopt::Long;


main: {
	binmode(STDIN, ":utf8");
	binmode(STDOUT, ":utf8");	

	my (%args) = ();

	GetOptions(
		'prefix=s' => \$args{"prefix"},
		'colname' => \$args{"colname"},
	);

	my $row = 0;
	my (@data) = ();

	# read
	foreach my $line ( <STDIN> ) {
		$line =~ s/\s+$//;

		my (@cols) = split(/\t/, $line);
		for( my $i=0 ; $i<scalar(@cols) ; $i++ ) {
			$data[$i][$row] = $cols[$i];
		}
		$row++;
	}

	# save
	for( my $i=0 ; $i<scalar(@data) ; $i++ ) {
		my $fn = $args{"prefix"}."$i";

		if( $args{"colname"} ) {
			if( $i == 0 ) {
				$fn = $args{"prefix"}."src";
			} else {
				$fn = $args{"prefix"}."ref$i";
			}
		}

		rmdir($fn);

		unless( open(FILE, ">$fn") ) {die "can not open : ".$!}
		binmode(FILE, "utf8");

		print FILE join("\n", @{$data[$i]});

		close(FILE);
	}
}


__END__


