#!/usr/bin/perl -w
#====================================================================
use strict;
use utf8;
use Encode;
use Getopt::Long;
use Tie::LevelDB; 
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
	my ($lm, $backoff) = ();

	$lm = new Tie::LevelDB::DB($args{"lm"}) if( defined($args{"lm"}) );
	$backoff = new Tie::LevelDB::DB($args{"backoff"}) if( defined($args{"backoff"}) );

	my $cnt = 0;
  	while( my $line = <STDIN> ) {
		$line =~ s/\s+$//;

		if( $line =~ /^ngram/ ) {
			my ($k, $v) = split(/=/, $line, 2);

			next if( !defined($v) );

			printf STDERR "[%s]:[%s]\n", $k, $v;

			$lm->Put($k, $v) if( defined($lm) );
			$backoff->Put($k, $v) if( defined($backoff) );
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

		$lm->Put($w, $p) if( defined($lm) );
		$backoff->Put($w, $b) if( defined($backoff) && defined($b) && $b ne "" );
	
		print STDERR "." if( ($cnt++ % 10000) == 0 );
	}
	print STDERR " done: $cnt\n";
}
#====================================================================
#====================================================================
__END__      

