#!/usr/bin/perl

use strict;
use utf8;
use Encode;
use Getopt::Long;

use FindBin qw($Bin);
use lib "$Bin";
require "smi.pm";


my (%args) = (
	"i" => 1,
	"th_dialog" => -1
);

GetOptions(
	"fn=s" => \$args{"fn"},
	"i=i" => \$args{"i"},
	"th_dialog=i" => \$args{"th_dialog"}
);


main: {
	binmode(STDIN, ":utf8");
	binmode(STDOUT, ":utf8");
	binmode(STDERR, ":utf8");

	my (%freq, @data) = ();
	foreach my $line ( <STDIN> ) {
		$line =~ s/^\s+|\s+$//g;

		my ($fn, $timeline, $en, $ko) = split(/\t/, $line);

		my ($start, $end) = split(/ \~ /, $timeline);

		$freq{$en}++;

		my (%item) = (
			"fn" => $fn, 
			"start" => $start, 
			"end" => $end, 
			"en" => $en, 
			"ko" => $ko
		);

		push(@data, \%item);
	}

	my (%dialog) = ();
	for( my $i=1 ; $i<scalar(@data)-1 ; $i++ ) {
		my (%prev) = (%{$data[$i-1]});
		my (%now)  = (%{$data[$i]});
		my (%next) = (%{$data[$i+1]});

		my $en = $now{"en"};
		next if( $freq{$en} < 10 );

		next if( $freq{$prev{"en"}} < 3 );
		next if( $freq{$next{"en"}} < 3 );


		printf "%d\t%d\t%d\t%s\t%s\t%s\t%s\n", 
				$freq{$en}, $freq{$prev{"en"}}, $freq{$next{"en"}},
				$en, $prev{"en"}, $en, $next{"en"};

		# $dialog{$en}{"front"}{$prev{"en"}}++;
		# $dialog{$en}{"next"}{$next{"en"}}++;
	}


	# foreach my $en ( keys %freq ) {
	# 	printf "%d\t%s\n", $freq{$en}, $en;
	# }
}


sub split_qa {
	my (@data) = (@{shift(@_)});

	my (@data2) = split_dash(\@data);

	for( my $i=1 ; $i<scalar(@data2) ; $i++ ) {
		my (%prev) = %{$data2[$i-1]};
		my (%next) = %{$data2[$i]};

		if( $prev{"en"} =~ /\?$/  && $next{"en"} !~ /\?/ ) {
			printf "%s ||| %s\t%s ||| %s\n", 
				$prev{"en"}, $prev{"ko"},
				$next{"en"}, $next{"ko"};
		}
	}
}


sub split_turn {
	# - How's the knee? - It's good.	- 무릎은? - 괜찮아

	my (@data) = (@{shift(@_)});

	for( my $i=0 ; $i<scalar(@data) ; $i++ ) {
		$data[$i]->{"ko"} =~ s/^\s*-\s*//;
		$data[$i]->{"en"} =~ s/^\s*-\s*//;

		my (@token_ko) = split(/-/, $data[$i]->{"ko"});
		my (@token_en) = split(/-/, $data[$i]->{"en"});

		if( scalar(@token_ko) > 1 && scalar(@token_ko) == scalar(@token_en) ) {
			for( my $j=0 ; $j<scalar(@token_ko) ; $j++ ) {
				$token_ko[$j] =~ s/^\s+//;
				$token_en[$j] =~ s/^\s+//;

				printf "%s ||| %s\t", $token_en[$j], $token_ko[$j];
			}

			printf "\n";
		}
	}
}


sub split_trigram {
	my (@data) = (@{shift(@_)});

	for( my $i=1 ; $i<scalar(@data)-1 ; $i++ ) {
		my (%prev) = (%{$data[$i-1]});
		my (%now)  = (%{$data[$i]});
		my (%next) = (%{$data[$i+1]});

		my $margin = $now{"start"} - $prev{"end"};
		next if( $margin > 5000 );

		$margin = $next{"start"} - $now{"end"};
		next if( $margin > 5000 );

		printf "%s ||| %s\t%s ||| %s\t%s ||| %s\n",
			$prev{"en"}, $prev{"ko"},
			$now{"en"}, $now{"ko"},
			$next{"en"}, $next{"ko"};
	}
}


sub split_bigram {
	my (@data) = (@{shift(@_)});

	for( my $i=1 ; $i<scalar(@data) ; $i++ ) {
		my (%prev) = (%{$data[$i-1]});
		my (%now) = (%{$data[$i]});

		my $margin = $now{"start"} - $prev{"end"};
		next if( $margin > 5000 );

		printf "%s ||| %s\t%s ||| %s\n",
			$prev{"en"}, $prev{"ko"},
			$now{"en"}, $now{"ko"};
	}
}


__END__
