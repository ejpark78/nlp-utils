#!/usr/bin/perl -w
#====================================================================
use strict;
use utf8;
use Encode;
use Getopt::Long;
use Tie::LevelDB; 
#====================================================================
my (%args) = (
	"separator" => " ||| ",
);

GetOptions(
	'fn|out=s' => \$args{"fn"},
	'sp|separator=s' => \$args{"separator"},
);
#====================================================================
binmode(STDIN, ":utf8");
binmode(STDOUT, ":utf8");
binmode(STDERR, ":utf8");
#====================================================================
main: {
	my $db = new Tie::LevelDB::DB($args{"fn"});

	my $cnt = 0;
  	while( my $line = <STDIN> ) {
		$line =~ s/\s+$//;
		
		my ($k, $v) = split(/\t/, $line, 2);

		next if( !defined($k) );

		$k =~ s/^\s+|\s+$//g;

		if( !defined($k) || !defined($v) || $k eq "" ) {
			$v = "" if( !defined($v) );
			printf STDERR "error: [%s]:[%s]\n", $k, $v;
			next;
		}

		# next if( $v eq "1" );
		
		$db->Put($k, $v);
	
		print STDERR "." if( $cnt++ % 10000 == 0 );
		print STDERR "($cnt)" if( $cnt % 100000 == 0 );
	}
	print STDERR " done: $cnt\n";
}
#====================================================================
#====================================================================
__END__      

