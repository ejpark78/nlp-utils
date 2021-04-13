#!/usr/bin/perl -w
#====================================================================
use strict;
use utf8;
use Encode;
use Getopt::Long;
#====================================================================
my (%args) = ();
GetOptions(
	"a=s" => \$args{"a"},
	"b=s" => \$args{"b"},
);
#====================================================================
binmode(STDIN, ":utf8");
binmode(STDOUT, ":utf8");
binmode(STDERR, ":utf8");
#====================================================================
main: {

	my (%data_a) = read_file($args{"a"});
	my (%data_b) = read_file($args{"b"});

	foreach my $sent ( keys %data_a ) {
		print "$sent\n" if( defined($data_b{$sent}) );
	}
}
#====================================================================
sub read_file {
	my $fn = shift(@_);

	my ($open_mode, $file_type) = ("<", `file $fn`);

	$open_mode = "<:gzip" if( $file_type =~ m/ gzip compressed data,/ );
	die "can not open : $fn $!\n" unless( open(FILE, $open_mode, $fn) );

	my (%data) = ();
	foreach my $line ( <FILE> ){
		$line =~ s/\s+/ /g;
		$line =~ s/^\s+|\s+$//g;

		$data{$line} = 1;
	}

	close(FILE);

	return (%data);
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
