#!/usr/bin/env perl
#!/usr/bin/perl
#====================================================================
use strict;
use Encode;
use XMLRPC::Lite;
use utf8;
use IPC::Open2;
use IPC::Open3;
use FileHandle;
use JSON;
use Getopt::Long;
#====================================================================
my (%args) = (
);

GetOptions(
	"th|threshold=s" => \$args{"threshold"},
	"debug" => \$args{"debug"}
);
#====================================================================
# MAIN
#====================================================================
main: {
	binmode(STDIN, "utf8");
	binmode(STDOUT, "utf8");
	binmode(STDERR, "utf8");

	my (@seq) = ();

	my $json = JSON->new;
	while( my $line = <STDIN> ) {
		$line =~ s/\s+$//;

		next if( $line eq "" );

		my (@t) = split(/\t/, $line);

		if( scalar(@seq) == 0 ) {
			(@seq) = (@t);
			next;
		}

		my (%data) = ();
		for( my $i=0 ; $i<scalar(@t) ; $i++ ) {
			last if( !defined($seq[$i]) );
			$data{$seq[$i]} = $t[$i];

			if( $seq[$i] =~ "detail" ) {
				$data{$seq[$i]} = parse_phrase_log($t[$i]);
			}
		}

		print $json->ascii(1)->encode( \%data )."\n";
	}
}
#====================================================================
sub parse_phrase_log {
	my $phrase = shift(@_);

	my (@ret) = ();
	foreach my $line ( split(/<\|\|\|>/, $phrase) ) {
		my ($src, $trg, $align) = split(/\|\|\|/, $line);
		my (%item) = (
			"ko" => $src,
			"en" => $trg,
			"align" => $align,
		);

		push(@ret, \%item);
	}

	return (\@ret);
}
#====================================================================
sub parse_sequence {
	my $sequence = shift(@_);

	my (@input_sequence) = ();
	foreach my $pos ( split(/,/, $sequence) ) {
		push(@input_sequence, $pos);
	}

	return (@input_sequence);
}
#====================================================================
sub parse_sequence_index {
	my $sequence = shift(@_);

	my $idx = 0;
	my (%input_sequence) = ();
	foreach my $pos ( split(/,/, $sequence) ) {
		$input_sequence{$pos} = $idx;
		$idx++;
	}

	return (%input_sequence);
}
#====================================================================
# sub functions
#====================================================================
#====================================================================
__END__

cat train-data/train-02.tok \
 | head -n10 \
 | cut -f2,3,4,5,6,8,10 \
 | ./to_json.pl -th 0.65 -seq tagged_text,source,lbmt,smt,phrase_log,smt_bleu,lbmt_bleu



2 : tagged_text
3 : source
4 : lbmt
5 : smt
6 : phrase_log
7 : ref


