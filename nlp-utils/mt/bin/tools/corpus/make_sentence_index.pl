#!/usr/bin/perl
#====================================================================
use strict;
use Encode;
use FileHandle;
use File::Path;
use Getopt::Long;
use BerkeleyDB; 
#====================================================================
my (%args) = (
);

GetOptions(
	"fn|out=s" => \$args{"fn"},
);
#====================================================================
# MAIN
#====================================================================
main: {
	binmode(STDIN, ":utf8");
	binmode(STDOUT, ":utf8");
	binmode(STDERR, ":utf8");

	my (%db);
	tie(%db, "BerkeleyDB::Btree", -Filename=>$args{"fn"}, -Flags=>DB_CREATE)
				or die("Cannot open ".$args{"fn"},": ".$!." ".$BerkeleyDB::Error."\n");

	my $cnt = 0;
	while( my $line = <STDIN> ) {
		printf STDERR "." if( $cnt++ % 1000 == 0 );
		printf STDERR "(%s)\n", comma($cnt) if( $cnt % 100000 == 0 );

		$line =~ s/\s+$//;

		$line = re_form($line);
		$line =~ s/\s+//g;

		if( $line ne "" ) {
			$db{$line} = 1;
		}
	}

	untie(%db);
}
#====================================================================
# sub functions
#====================================================================
sub re_form {
	my $str = shift(@_);

	$str =~ s/[:;@,-~%"'?!(){}\[\]|=_$&*]/ /g;

	return $str;
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

