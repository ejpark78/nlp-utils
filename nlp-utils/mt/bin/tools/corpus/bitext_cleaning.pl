#!/usr/bin/perl -w
#====================================================================
use strict;
use utf8;
use Encode;
use Getopt::Long;
use BerkeleyDB; 
use TryCatch;
#====================================================================
my (%args) = ( 
	# "th" => 0.9
);
GetOptions(
	# "th=f" => \$args{"th"}
);
#====================================================================
binmode(STDIN, ":utf8");
binmode(STDOUT, ":utf8");
binmode(STDERR, ":utf8");
#====================================================================
main: {
	my $s_id = 0;
	while( my $line = <STDIN> ) {
		$line =~ s/\s+$//;
		
		my ($giza_e2f, $giza_f2e, $es, $en) = split(/\t/, $line, 4);

		my (@token_es) = split(/\s+/, $es);
		my (@token_en) = split(/\s+/, $en);

		# my (@ngram_es, @ngram_en) = ();
		# get_ngram(\@token_en, 1, \@ngram_en);
		# get_ngram(\@token_es, 1, \@ngram_es);

		try {
			my $score = (log($giza_e2f) / scalar(@token_en)) + (log($giza_f2e) / scalar(@token_es));

			printf "%f\t%s\t%s\n", $score, $es, $en;
		} catch($err) {
			printf STDERR "%s\n", $err;
			printf STDERR "%s\n", $line;
		}

		# foreach my $en ( @ngram_en ) {
		# 	foreach my $es ( @ngram_es ) {
		# 		printf "%s %s\n", $en, $es;
		# 	}
		# }

		$s_id++;

		printf STDERR "." if( $s_id % 10000 == 0 );
		printf STDERR "(%s)\n", comma($s_id) if( $s_id % 1000000 == 0 );
	}

}
#====================================================================
our (%stop_word) = (
	"." => 1,
	"," => 1,
	"%" => 1,
	"!" => 1,
	"..." => 1,
	"?" => 1,
	":" => 1,
	";" => 1,
);

sub get_ngram {
	my (@token) = (@{shift(@_)});
	my $n = shift(@_);
	my $ngram = shift(@_);

	$n--;

	return if( scalar(@token) < $n );	

	# <s> he have the car </s>
	# unshift(@token, "<s>");
	# push(@token, "</s>");

	for( my $i=0 ; $i<scalar(@token)-$n ; $i++ ) {
		my (@n_list) = @token[$i..($i+$n)];

		my $stop = 0;
		for( my $j=0 ; $j<scalar(@n_list)-1 ; $j++ ) {
			if( defined($stop_word{$n_list[$j]}) ) {
				$stop = 1;
				last;
			}
		}
		next if( $stop == 1 );

		my $buf = join(" ", @n_list);

		# printf "$n: %s\n", $buf;

		$buf =~ s/\s+$//;
		$buf =~ s/^(<s> )+/<s> /;
		$buf =~ s/( <\/s>)+$/ <\/s>/;

		next if( $buf eq "" );

		push(@{$ngram}, $buf);
	}
}
#====================================================================
sub comma {
	my $cnt = shift(@_);

	$cnt = sprintf("%d", $cnt);
	for ( my $i = -3; $i > -1 * length($cnt); $i -= 4 ){
	    substr( $cnt, $i, 0 ) = ',';
	}

	return $cnt;
}
#====================================================================
__END__      

