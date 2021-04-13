#!/usr/bin/perl
#====================================================================
use strict;
use Encode;
use FileHandle;
use File::Path;
use Getopt::Long;
#====================================================================
my (%args) = (
	"fields" => "1",
	"threshold" => "0.7-0.7"
);

GetOptions(
	"f|fields=i" => \$args{"fields"},
	"th|threshold=s" => \$args{"threshold"},
);
#====================================================================
# MAIN
#====================================================================
main: {
	grouping_column(\%args);	
}
#====================================================================
# sub functions
#====================================================================
sub grouping_column {
	binmode(STDIN, ":utf8");
	binmode(STDOUT, ":utf8");
	binmode(STDERR, ":utf8");

	my (%param) = (%{shift(@_)});
	$param{"fields"}--;

	# 0.7-0.7
	my ($th_start, $th_end) = ();

	if( defined($param{"threshold"}) ) {
		($th_start, $th_end) = split(/-/, $param{"threshold"});

		$th_start = undef if( !defined($th_start) || $th_start eq "" );
		$th_end = undef if( !defined($th_end) || $th_end eq "" );

		# print STDERR $param{"threshold"}."\n";
		# print STDERR "($th_start, [$th_end])\n";
	}

	my (%ngram) = ();
	while( my $line = <STDIN> ) {
		$line =~ s/\s+$//;

		next if( $line eq "" );
		next if( $line =~ /^#/ );

		my (@t) = split(/\t/, $line);

		push(@{$ngram{$t[$param{"fields"}]}}, $line);
	}

	foreach my $score ( keys %ngram ) {
		next if( defined($th_start) && $score < $th_start );
		next if( defined($th_end) && $score >= $th_end );

		foreach my $str ( @{$ngram{$score}} ) {
			printf "%.1f\t%s\n", $score, $str;
		}
	}
}
#====================================================================
__END__

