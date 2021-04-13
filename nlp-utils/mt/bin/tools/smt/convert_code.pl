#!/usr/bin/perl
#====================================================================
use strict;
use Encode;
use FileHandle;
use File::Path;
use Getopt::Long;
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

	while( my $line=<STDIN> ) {
		$line =~ s/^\s+|\s+$//g;

		$line =~ s/\t/@@@@@/g;


		$line =~ s/&lt;/</g;
		$line =~ s/&gt;/>/g;
		$line =~ s/&amp;/&/g;
		$line =~ s/&apos;/'/g;
		$line =~ s/&quot;/"/g;
		$line =~ s/&nbsp;/ /g;
		$line =~ s/&#(\d+);/chr($1)/eg;

		$line =~ s/^-//;
		$line =~ s/^\s+|\s+$//g;
		$line =~ s/^"//;
		$line =~ s/^\s+|\s+$//g;
		$line =~ s/"$//;
		$line =~ s/^\s+|\s+$//g;
		$line =~ s/ -/ /g;
		$line =~ s/^\s+|\s+$//g;
		$line =~ s/\s+/ /g;

		$line =~ s/^.+? -> .+?,\s*//;

		$line =~ s/@@@@@/\t/g;

		print "$line\n";
	}
}
#====================================================================
# sub functions
#====================================================================
#====================================================================
__END__



    # $text =~ s/\&/\&amp;/g;   # escape escape
    # $text =~ s/\|/\&#124;/g;  # factor separator
    # $text =~ s/\</\&lt;/g;    # xml
    # $text =~ s/\>/\&gt;/g;    # xml
    # $text =~ s/\'/\&apos;/g;  # xml
    # $text =~ s/\"/\&quot;/g;  # xml
    # $text =~ s/\[/\&#91;/g;   # syntax non-terminal
    # $text =~ s/\]/\&#93;/g;   # syntax non-terminal

