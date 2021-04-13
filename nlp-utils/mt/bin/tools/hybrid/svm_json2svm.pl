#!/usr/bin/perl
#====================================================================
use strict;
use Encode;
use FileHandle;
use File::Path;
use Getopt::Long;
use POSIX;
use Data::Dumper;
use JSON;
use BerkeleyDB;

use FindBin qw($Bin);
use lib "$Bin";

require "hybrid.pm";
#====================================================================
our (%args) = ();

GetOptions(
	"debug" => \$args{"debug"},
);
#====================================================================
# MAIN
#====================================================================
main: {
	binmode(STDIN, ":utf8");
	binmode(STDOUT, ":utf8");
	binmode(STDERR, ":utf8");

	# extract features
	my $cnt = 0;
	my $json = JSON->new->allow_nonref;
	while( my $line = <STDIN> ) {
		$line =~ s/\s+$//;

		next if( $line eq "" );

		my $features = $json->decode( $line );
		my $class = get_class(\%model, $input, $features);

		my $i = 1;
		my (@result) = ();
		foreach my $m ( sort keys %{$features} ) {
			foreach my $t ( sort keys %{$features->{$m}} ) {
				push(@result, sprintf("%d:%s", $i++, $features->{$m}{$t}));
			}
		}

		printf "%s %s\n", $model{$class}, join(" ", @result);

		printf STDERR "\r(%07d)", $cnt if( $cnt++ % 10 == 0 );
	}

	printf STDERR "(%07d)\n", $cnt++;
}
#====================================================================
__END__

