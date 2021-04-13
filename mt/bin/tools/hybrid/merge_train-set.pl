#!/usr/bin/perl -w

use strict;
use utf8;
use Getopt::Long;
use BerkeleyDB; 


my (%args) = (
	"upper" => -1,
	"lower" => -1,
);

GetOptions(
	'fn|out=s' => \$args{"fn"},
	'upper=i' => \$args{"upper"},
	'lower=i' => \$args{"lower"},
);


# binmode(STDIN, ":utf8");
# binmode(STDOUT, ":utf8");
# binmode(STDERR, ":utf8");


main: {
	my (%db);
	tie(%db, "BerkeleyDB::Btree", -Filename=>$args{"fn"}, -Flags=>DB_CREATE)
				or die("Cannot open ".$args{"fn"},": ".$!." ".$BerkeleyDB::Error."\n");

	my $cnt = 0;
  	while( my $line = <STDIN> ) {
		$line =~ s/\s+$//;
		
		my ($k, $v) = split(/\t/, $line, 2);

		next if( !defined($k) );

		if( defined($db{$k}) ) {
			printf "%s\n", $db{$k};
		} else {
			$k =~ s/\s+//g;
			if( defined($db{$k}) ) {
				printf "%s\n", $db{$k};
			} else {
				printf STDERR "ERROR: %s\n", $k;
				
			}
		}
	
		printf STDERR "\r(%s)", comma($cnt) if( $cnt++ % 10000 == 0 );
	}

	untie(%db);
}


sub comma {
	my $cnt = shift(@_);

	$cnt = reverse join ",", (reverse $cnt) =~ /(\d{1,3})/g;

	return $cnt;
}


__END__      

