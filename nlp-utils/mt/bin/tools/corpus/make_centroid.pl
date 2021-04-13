#!/usr/bin/perl -w
#====================================================================
use strict;
use utf8;
use Encode;
use Getopt::Long;
use BerkeleyDB; 
#====================================================================
my (%args) = ( 
	"th" => 0.9,
	"fn_tf" => "data.en.db",
	"fn_centroid" => "tm200.en.n3.db",
);
GetOptions(
	"th=f" => \$args{"th"},
	"fn_tf=s" => \$args{"fn_tf"},
	"fn_centroid=s" => \$args{"fn_centroid"},
);
#====================================================================
binmode(STDIN, ":utf8");
binmode(STDOUT, ":utf8");
binmode(STDERR, ":utf8");
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

main: {
	my (%centroid);
	tie(%centroid, "BerkeleyDB::Btree", -Filename=>$args{"fn_centroid"}, -Flags=>DB_CREATE)
				or die("Cannot open ".$args{"fn_centroid"},": ".$!." ".$BerkeleyDB::Error."\n");

	my (%tf);
	tie(%tf, "BerkeleyDB::Btree", -Filename=>$args{"fn_tf"}, -Flags=>DB_CREATE)
				or die("Cannot open ".$args{"fn_tf"},": ".$!." ".$BerkeleyDB::Error."\n");

	my (@n_list) = split(/,/, $centroid{"_NGRAM_"});

	my $s_id = 0;
	while( my $line = <STDIN> ) {
		$line =~ s/\s+$//;
		
		my ($es, $en) = split(/\t/, $line, 2);

		my (@token) = split(/\s+/, $en);

		my (@ngram) = ();
		foreach my $n ( @n_list ) {
			get_ngram(\@token, $n, \@ngram);
		}

		my (%sum) = ("a" => 0, "b" => 0, "c" => 0);
		foreach my $w ( @ngram ) {
			next if( !defined($tf{$w}) );
			next if( !defined($centroid{$w}) );

			$sum{"a"} += $centroid{$w} * $tf{$w};
			$sum{"b"} += $centroid{$w} * $centroid{$w};
			$sum{"c"} += $tf{$w} * $tf{$w};
		}

		my $base = sqrt($sum{"b"}) * sqrt($sum{"c"});
		my $cos = ( $base > 0 ) ? $sum{"a"} / $base : 0;

		if( $args{"th"} <= $cos ) {
			printf "%f\t%s\t%s\n", $cos, $en, $es;
		}

		$s_id++;

		printf STDERR "." if( $s_id % 10000 == 0 );
		printf STDERR "(%s)\n", comma($s_id) if( $s_id % 1000000 == 0 );
	}

	untie(%tf);
	untie(%centroid);
}
#====================================================================
sub get_ngram {
	my (@token) = (@{shift(@_)});
	my $n = shift(@_);
	my $ngram = shift(@_);

	$n--;

	return if( scalar(@token) < $n );	

	# <s> he have the car </s>
	unshift(@token, "<s>");
	push(@token, "</s>");

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

