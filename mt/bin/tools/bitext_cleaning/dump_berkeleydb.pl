#!/usr/bin/perl
#====================================================================
use strict;
use Encode;
use Getopt::Long;
use BerkeleyDB; 
#====================================================================
my (%args) = ();
GetOptions();
#====================================================================
# MAIN
#====================================================================
main: {
	binmode(STDIN, ":utf8");
	binmode(STDOUT, ":utf8");
	binmode(STDERR, ":utf8");

	if (!@ARGV) {
	    @ARGV = <STDIN>;
	    chop(@ARGV);
	}

	foreach my $fn ( @ARGV ) {
		printf STDERR "fn: %s\n", $fn;
		
		my (%db) = ();
		tie(%db, "BerkeleyDB::Btree", -Filename=>$fn, -Flags=>DB_CREATE)
					or die("Cannot open ".$fn,": ".$!." ".$BerkeleyDB::Error."\n");

		foreach my $k ( keys %db ) {
			print "$k\t$db{$k}\n";
		}

		untie(%db);
	}
}
#====================================================================
sub comma {
	my $cnt = shift(@_);

	$cnt = reverse join ",", (reverse $cnt) =~ /(\d{1,3})/g;

	return $cnt;
}
#====================================================================
#====================================================================
__END__


