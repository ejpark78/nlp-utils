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
);
#====================================================================
# MAIN
#====================================================================
main: {
	binmode(STDIN, ":utf8");
	binmode(STDOUT, ":utf8");
	binmode(STDERR, ":utf8");

	my (%sent_break) = ();

	while( my $line=<STDIN> ) {
		$line =~ s/\s+$//;

		my ($ko, $es) = split(/\t/, $line);

		$ko =~ s/<br>/\t/g;
		$es =~ s/<br>/\t/g;

		foreach my $k ( split(/\t/, $ko) ) {
			foreach my $e ( split(/\t/, $es) ) {
				$sent_break{"$k\t$e"} = 1;	
			}
		}
	}

	my $sep = "\\\||\-|\\\/";

	my (%uniq) = ();
	foreach my $line ( keys %sent_break ) {
		my ($ko, $es) = split(/\t/, $line);

		my (@t_ko) = split(/$sep/, $ko);
		my (@t_es) = split(/$sep/, $es);

		for( my $i=0 ; $i<scalar(@t_ko) ; $i++ ) {$t_ko[$i] =~ s/^\s+|\s+$//g}
		for( my $i=0 ; $i<scalar(@t_es) ; $i++ ) {$t_es[$i] =~ s/^\s+|\s+$//g}

		if( scalar(@t_ko) > 1 && scalar(@t_ko) == scalar(@t_es) ) {
			for( my $i=0 ; $i<scalar(@t_ko) ; $i++ ) {
				$uniq{sprintf "%s\t%s", $t_ko[$i], $t_es[$i]} = 1;
			}
		}

		$uniq{sprintf "%s\t%s", join(" ", @t_ko), join(" ", @t_es)} = 1;
	}

	foreach my $line ( sort keys %uniq ) {
		print "$line\n";
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
__END__


