#!/usr/bin/perl -w
#====================================================================
use strict;
use utf8;
use Getopt::Long;
use Tie::LevelDB; 
#====================================================================
my (%args) = (
);

GetOptions(
	"lm=s" => \$args{"lm"},
);
#====================================================================
binmode(STDIN, ":utf8");
binmode(STDOUT, ":utf8");
binmode(STDERR, ":utf8");
#====================================================================
main: {
	my (%ngram_db) = ();
	$ngram_db{"lm"} = new Tie::LevelDB::DB($args{"lm"}) if( defined($args{"lm"}) && -e $args{"lm"} );

	my $cnt = 0;
	my (%data) = ();
	while( my $line = <STDIN> ) {
		$line =~ s/\s+$//;

		my ($f, $e, $p) = split(/ \|\|\| /, $line);
		next if( !defined($f) || !defined($e) );

		($p) = split(/ /, $p);

		if( !defined($ngram_db{"lm"}) ) {
			$data{$f} .= " ||| " if( defined($data{$f}) );
			$data{$f} .= sprintf("%s\t%f", $e, $p);
		} else {
			next if( defined($data{$f}) );
			next if( !defined($ngram_db{"lm"}->Get($f)) );
 
			$data{$f} = $ngram_db{"lm"}->Get($f);
			print "$f\t".$ngram_db{"lm"}->Get($f)."\n";
		}

		print STDERR "." if( $cnt++ % 100000 == 0 );
		print STDERR "($cnt)" if( $cnt % 1000000 == 0 );
	}

	print STDERR " DONE ($cnt)\n";

	if( !defined($ngram_db{"lm"}) ) {
		foreach my $w ( keys %data ) {
			print "$w\t".$data{$w}."\n";
		}
	}
}
#====================================================================
__END__