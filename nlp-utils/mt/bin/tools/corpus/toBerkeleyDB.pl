#!/usr/bin/perl -w
#====================================================================
use strict;
use utf8;
use Encode;
use Getopt::Long;
use BerkeleyDB; 
#====================================================================
my (%args) = (
	"upper" => -1,
	"lower" => 1,
	"total" => -1,
);

GetOptions(
	'fn|out=s' => \$args{"fn"},
	'ngram=s' => \$args{"ngram"},
	'upper=i' => \$args{"upper"},
	'lower=i' => \$args{"lower"},
	'total=i' => \$args{"total"},
);
#====================================================================
binmode(STDIN, ":utf8");
binmode(STDOUT, ":utf8");
binmode(STDERR, ":utf8");
#====================================================================
main: {
	my (%db);
	tie(%db, "BerkeleyDB::Btree", -Filename=>$args{"fn"}, -Flags=>DB_CREATE)
				or die("Cannot open ".$args{"fn"},": ".$!." ".$BerkeleyDB::Error."\n");

	my $cnt = 0;
	my $total_word_freq = 0;
  	while( my $line = <STDIN> ) {
		$line =~ s/\s+$//;
		
		my ($k, $v) = split(/\t/, $line, 2);

		next if( !defined($k) );

		$k =~ s/^\s+|\s+$//g;

		if( !defined($k) || !defined($v) || $k eq "" ) {
			$v = "" if( !defined($v) );
			printf STDERR "error: [%s]:[%s]\n", $k, $v;
			next;
		}
		
		if( $args{"lower"} > 0 && $v <= $args{"lower"} ) {
			printf STDERR "(%s:$v)", $k, $v;
			next;
		}

		if( $args{"upper"} > 0 && $v >= $args{"upper"} ) {
			printf STDERR "(%s:$v)", $k, $v;
			next;
		}

		$v /= $args{"total"} if( $args{"total"} > 0 );
		$db{$k} = $v;

		$total_word_freq += $v;
	
		printf STDERR "." if( $cnt++ % 10000 == 0 );
		printf STDERR "(%s)\n", comma($cnt) if( $cnt % 1000000 == 0 );
	}

	$db{"_NGRAM_"} = $args{"ngram"};
	$db{"_TOTAL_WORD_COUNT_"} = $cnt;
	$db{"_TOTAL_WORD_FREQ_"} = $total_word_freq;

	untie(%db);
	print STDERR "\n_TOTAL_WORD_COUNT_ : $cnt, _TOTAL_WORD_FREQ_ : $total_word_freq \n";
}
#====================================================================
sub comma {
	my $cnt = shift(@_);

	$cnt = reverse join ",", (reverse $cnt) =~ /(\d{1,3})/g;

	return $cnt;
}
#====================================================================
__END__      

