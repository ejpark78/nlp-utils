#!/usr/bin/perl -w
#====================================================================
use strict;
use utf8;
use Encode;
use Getopt::Long;
use BerkeleyDB; 
use Math::BigFloat;
#====================================================================
my (%args) = ( 
	"fn" => ""
);
GetOptions(
	"fn=s" => \$args{"fn"}
);
#====================================================================
binmode(STDIN, ":utf8");
binmode(STDOUT, ":utf8");
binmode(STDERR, ":utf8");
#====================================================================
main: {
	# $args{"fn"} = "lex.e2f.db";

	my (%db);
	tie(%db, "BerkeleyDB::Btree", -Filename=>$args{"fn"}, -Flags=>DB_CREATE)
				or die("Cannot open ".$args{"fn"},": ".$!." ".$BerkeleyDB::Error."\n");

	my $s_id = 0;

	my $buf = "";
	while( my $line = <STDIN> ) {
		$line =~ s/\s+$//;
		
		# vasospasm vasospasmo 1.0000000
		# vasospasm espasmo 0.0200000
		# vasospasm pulmón 0.0037594
		# vasospasm vascular 0.0217391
		# vasospasm de 0.0000009

		my ($a, $b, $score) = split(/ /, $line, 3);

		$score =~ s/^\s+|\s+$//g;

		my $key = sprintf("%s %s", $a, $b);
		$db{$key} = $score;

		# printf "%s\t%s\n", $key, $score;

		$s_id++;

		printf STDERR "." if( $s_id % 10000 == 0 );
		printf STDERR "(%s)\n", comma($s_id) if( $s_id % 1000000 == 0 );
	}

	untie(%db);
}
#====================================================================
sub comma {
	my $cnt = shift(@_);

	$cnt = sprintf("%d", $cnt);
	for ( my $i = -3; $i > -1 * length($cnt); $i -= 4 ){
	    substr( $cnt, $i, 0 ) = ',';
	}

	return $cnt;
}
#====================================================================
__END__      

