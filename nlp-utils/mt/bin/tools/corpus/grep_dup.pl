#!/usr/bin/perl
#====================================================================
use strict;
use Encode;
use FileHandle;
use File::Path;
use Getopt::Long;
use Tie::LevelDB; 
use POSIX;
#====================================================================
my (%args) = (
);

GetOptions(
	"f=s" => \$args{"f"},
);
#====================================================================
# MAIN
#====================================================================
main: {
	binmode(STDIN, ":utf8");
	binmode(STDOUT, ":utf8");
	binmode(STDERR, ":utf8");

	# read compare file
	my $fn = $args{"f"};
	my ($open_mode, $file_type) = ("<", `file $fn`);

	$open_mode = "<:gzip" if( $file_type =~ m/ gzip compressed data,/ );
	die "can not open : $fn $!\n" unless( open(FILE, $open_mode, $fn) );

	my $cnt = 0;
	my (%index) = ();
	foreach my $line ( <FILE> ) {
		$line =~ s/^\s+|\s+$//g;	
		$line =~ s/\s+//g;	

		$index{$line}++;

		printf STDERR "%s\r", comma($cnt) if( $cnt++ % 100000 == 0 );
	}
	printf STDERR "%s\n", comma($cnt);

	close(FILE);

	while( my $line=<STDIN> ) {
		my $needle = $line;

		$needle =~ s/^\s+|\s+$//g;
		$needle =~ s/\s+//g;	

		if( defined($index{$needle}) ) {
			print $line;
		}
	}
}
#====================================================================
# sub functions
#====================================================================
sub comma {
	my $cnt = shift(@_);

	$cnt = reverse join ",", (reverse $cnt) =~ /(\d{1,3})/g;

	return $cnt;
}
#====================================================================
#====================================================================
__END__


