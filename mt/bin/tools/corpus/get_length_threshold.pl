#!/usr/bin/perl
#====================================================================
use strict;
use Encode;
use FileHandle;
use File::Path;
use Getopt::Long;
use Tie::LevelDB; 
use POSIX;
#====================================================================
my (%args) = (
	"l1" => 0,
	"l2" => 1,
);

GetOptions(
	"l1=i" => \$args{"l1"},
	"l2=i" => \$args{"l2"},
);
#====================================================================
# MAIN
#====================================================================
main: {
	binmode(STDIN, ":utf8");
	binmode(STDOUT, ":utf8");
	binmode(STDERR, ":utf8");

	my $cnt = 0;
	my (%count, %sum) = ();
	while( my $line=<STDIN> ) {
		$line =~ s/^\s+|\s+$//g;

		print STDERR "." if( $cnt++ % 100000 == 0 );
		printf STDERR "(%s)", comma($cnt) if( $cnt % 1000000 == 0 );

		my (@token) = split(/\t/, $line);

		my $a = $token[$args{"l1"}];
		my $b = $token[$args{"l2"}];

		next if( !defined($a) || !defined($b) );
		next if( $a =~ /^\s*$/ || $b =~ /^\s*$/ );

	    	my (@tok_a)=split(/\s+/, $a);
	    	my (@tok_b)=split(/\s+/, $b);

	    	$sum{scalar(@tok_a)}++; 
	    	$count{scalar(@tok_a)}{scalar(@tok_b)}++; 
	}

	my $total_sum = 0;
	my $total_cutoff = 0;
	foreach my $cnt_src ( sort {$a<=>$b} keys %count ) {
		my $avg_length = 0;
		foreach my $cnt_trg ( keys %{$count{$cnt_src}} ) {
			$avg_length += $cnt_trg * $count{$cnt_src}{$cnt_trg};
		}

		$avg_length = $avg_length / $sum{$cnt_src};

		my $corrl = 0;
		foreach my $cnt_trg ( keys %{$count{$cnt_src}} ) {
			$corrl += ($avg_length - $cnt_trg) * ($avg_length - $cnt_trg) * $count{$cnt_src}{$cnt_trg};
		}

		$corrl = sqrt($corrl / $sum{$cnt_src});

		my $cut_off = 0;
		foreach my $cnt_trg ( keys %{$count{$cnt_src}} ) {
			$cut_off += $count{$cnt_src}{$cnt_trg} if( $cnt_trg > ($avg_length + $corrl) );  
			$cut_off += $count{$cnt_src}{$cnt_trg} if( $cnt_trg < ($avg_length - $corrl) );  
		}

		$total_sum += $sum{$cnt_src};
		$total_cutoff += $cut_off;

		printf "%03d\tavg: %3.5f\tcorrl: %3.5f\tcut_off: %03d\t%0.3f\n", 
			$cnt_src, $avg_length, $corrl, $cut_off, $cut_off/$sum{$cnt_src};
	}

	printf "total cutoff rate: %0.3f, total cutoff: %d, total sum: %d\n", 
		$total_cutoff/$total_sum, $total_cutoff, $total_sum;
}
#====================================================================
# sub functions
#====================================================================
sub comma {
	my $cnt = shift(@_);

	$cnt = reverse join ",", (reverse $cnt) =~ /(\d{1,3})/g;

	return $cnt;
}
#====================================================================
#====================================================================
__END__


