#!/usr/bin/perl -w

use strict;
use utf8;
use Encode;
use Getopt::Long;

my (%args) = ();

GetOptions(
	"c" => \$args{"c"},
	"c2" => \$args{"c2"},
	"r|reverse" => \$args{"reverse"},
);


binmode(STDIN, ":utf8");
binmode(STDOUT, ":utf8");
binmode(STDERR, ":utf8");


main: {
	my $total = 0;
	my (%uniq) = ();
	while( my $line=<STDIN> ) {
		$line =~ s/\s+$//;
		$uniq{$line}++;
		$total++;
	}
	
	my (@data) = ();
	if( $args{"reverse"} ) {
		(@data) = (sort keys %uniq);
	} else {
		(@data) = (sort {$b cmp $a} keys %uniq);
	}

	foreach my $line ( @data ) {
		if( $args{"c"} ) {
			printf "%s\t%s\n", $line, comma($uniq{$line});
		} elsif( $args{"c2"} ) {
			printf "%d\t%s\n", $uniq{$line}, $line;
		} else {
			print "$line\n";
		}
	}

	if( $args{"c"} || $args{"c2"} ) {
		printf "total: %s\n", comma($total);
	}
}

sub comma {
	my $cnt = shift(@_);

	$cnt = sprintf("%d", $cnt);
	for ( my $i = -3; $i > -1 * length($cnt); $i -= 4 ){
	    substr( $cnt, $i, 0 ) = ',';
	}

	return $cnt;
}


__END__
