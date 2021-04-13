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

	my $cnt = 0;
	while( my $line=<STDIN> ) {
		$line =~ s/^\s+|\s+$//g;

		print STDERR "." if( $cnt++ % 100000 == 0 );
		printf STDERR "(%s)", comma($cnt) if( $cnt % 1000000 == 0 );

		my ($a,$b) = split(/\t/, $line, 2);
		next if( $a =~ /^\s*$/ || $b =~ /^\s*$/ );

	    my (@tok_a)=split(/\s+/, $a);
	    my (@tok_b)=split(/\s+/, $b);

	    my (%idx) = ();
	    foreach my $w ( @tok_a ) {
	    	$idx{$w}++;
	    }
	    foreach my $w ( @tok_b ) {
	    	$idx{$w}++;
	    }

	    my ($max_w, $max) = ("", -1);
	    foreach my $w ( keys %idx ) {
	    	$max_w = $w, $max = $idx{$w} if( $idx{$w} > $max );
	    }

	    # printf "%d\t%s\t%s\n", $max, $max_w, $line;

	    next if( $max > 5 );
	    next if( $max > 2 && $max_w !~ /[a-zA-Z]/ );
	    printf "%s\n", $line;

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


