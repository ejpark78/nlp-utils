#!/usr/bin/perl -w
#====================================================================
use strict;
use utf8;
use Encode;
use Getopt::Long;
use BerkeleyDB;
#====================================================================
my (%args) = ();

GetOptions(
	'lm=s' => \$args{"lm"},
	'backoff=s' => \$args{"backoff"},
);
#====================================================================
binmode(STDIN, ":utf8");
binmode(STDOUT, ":utf8");
binmode(STDERR, ":utf8");
#====================================================================
main: {
	my (%lm);
	tie(%lm, "BerkeleyDB::Btree", -Filename=>$args{"lm"}, -Flags=>DB_CREATE -Cachesize=>2*1024*1024*1024)
	                        or die("Cannot open ".$args{"lm"},": ".$!." ".$BerkeleyDB::Error."\n");

	my (%backoff);
	tie(%backoff, "BerkeleyDB::Btree", -Filename=>$args{"backoff"}, -Flags=>DB_CREATE -Cachesize=>2*1024*1024*1024)
	                        or die("Cannot open ".$args{"backoff"},": ".$!." ".$BerkeleyDB::Error."\n");

	my $cnt = 0;
  	while( my $line = <STDIN> ) {
		$line =~ s/\s+$//;

		if( $line =~ /^ngram/ ) {
			my ($k, $v) = split(/=/, $line, 2);

			next if( !defined($v) );

			printf STDERR "[%s]:[%s]\n", $k, $v;

			$lm{$k} = $v;
			$backoff{$k} = $v;
			next;
		}

		# lm		
		my ($p, $w, $b) = split(/\t/, $line, 3);

		if( !defined($w) || !defined($p) || $w eq "" ) {
			$w = "" if( !defined($w) );
			$p = "" if( !defined($p) );
			$b = "" if( !defined($b) );

			printf STDERR "error: [%s]:[%s]:[%s]\n", $w, $p, $b;
			next;
		}

		$w =~ s/^\s+|\s+$//g;

		$lm{$w} = $p;
		$backoff{$w} = $b if( defined($b) && $b ne "" );
	
		print STDERR "." if( ($cnt++ % 10000) == 0 );
	}
	print STDERR " done: $cnt\n";

	untie(%lm);
	untie(%backoff);
}
#====================================================================
#====================================================================
__END__      

