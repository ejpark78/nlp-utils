#!/usr/bin/perl
#====================================================================
use strict;
use utf8;
use Encode;
use Getopt::Long;
#====================================================================
my (%args) = (  
	'th' => 1,
	'condition' => "lt"
);

GetOptions(
  's|seq|sequence=s' => \$args{"sequence"},
  't|th|threshold=f' => \$args{"threshold"},
  'c|cond|condition=s' => \$args{"condition"},
);
#====================================================================
binmode STDOUT, ":utf8";
binmode STDERR, ":utf8";
#====================================================================
main: {
	my (%sequence) = parse_sequence($args{"sequence"});

	my (%data) = ();

	my $cnt = 0;
	# bleu \t length ... \n
	while( my $line = <STDIN> ) {
		$line =~ s/\s+$//;
		next if( $line eq "" || $line =~ /^#/ );

		my (@t) = split(/\t/, $line);

		my $score = $t[$sequence{"score"}];

		# < > <= >= lt gt le ge
		if( $args{"condition"} eq "gt" && $score > $args{"threshold"} ) {
			$data{"1"}++;			
		} elsif( $args{"condition"} eq "lt" && $score < $args{"threshold"} ) {
			$data{"1"}++;			
		} elsif( $args{"condition"} eq "le" && $score <= $args{"threshold"} ) {
			$data{"1"}++;			
		} elsif( $args{"condition"} eq "ge" && $score >= $args{"threshold"} ) {
			$data{"1"}++;			
		} elsif( $args{"condition"} eq "eq" && $score == $args{"threshold"} ) {
			$data{"1"}++;			
		} else {
			$data{"0"}++;
		}

		$data{"sum"} += $score;

		$cnt++;
	}

	printf "condition: %s, avg:%f, 0:%d, 1:%d, threshold:%f, ratio:%.1f\n", 
		$args{"condition"}, $data{"sum"}/$cnt, 
		$data{"0"},  $data{"1"}, 
		$args{"threshold"}, $data{"1"}/$cnt*100;
}
#====================================================================
sub parse_sequence {
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
__END__
