#!/usr/bin/perl

use strict;

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

__END__

