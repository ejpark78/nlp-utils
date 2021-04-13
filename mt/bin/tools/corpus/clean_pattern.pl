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

		# next if( $line =~ /\[|\]|\{|\}|\(|\)|\<|\>/ );
		$line =~ s/\[.+?\]//g;
		$line =~ s/\(.+?\)//g;
		$line =~ s/\{.+?\}//g;
		$line =~ s/\<.+?\>//g;

		$line =~ s/(\[|\(|\{|\<).+?(\]|\)|\}|\>)//g;

		my ($a,$b) = split(/\t/, $line, 2);
		next if( $a =~ /^\s*$/ || $b =~ /^\s*$/ );

		next if( $a !~ /\p{Hangul}/ );
		next if( $b !~ /[a-zA-Z]/ );

	    my (@tok_a) = split(/\s+/, $a);
	    my (@tok_b) = split(/\s+/, $b);

	    next if( scalar(@tok_a) > 40 );
	    next if( scalar(@tok_b) > 40 );

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
__END__


