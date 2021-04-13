#!/usr/bin/perl
#====================================================================
use strict;
use Encode;
use FileHandle;
use File::Path;
use Getopt::Long;
use Tie::LevelDB; 
use POSIX;
use Math::Complex;
#====================================================================
my (%args) = (
	"c" => 3,
);

GetOptions(
	# "th|threshold=s" => \$args{"threshold"},
	"c=f" => \$args{"c"},
	"debug" => \$args{"debug"}
);
#====================================================================
# MAIN
#====================================================================
main: {
	binmode(STDIN, ":utf8");
	binmode(STDOUT, ":utf8");
	binmode(STDERR, ":utf8");

	my $svm_form = 0;

	my $cnt = 0;
	my (@sum, @data, @class) = ();
	while( my $line=<STDIN> ) {
		$line =~ s/\s+$//;

		my ($c, @f) = split(/\s+/, $line);
		for( my $i=0 ; $i<scalar(@f) ; $i++ ) {
			$sum[$i] += $f[$i];
		}

		if( $f[0] =~ m/\d+:\d+/ ) {
			$svm_form = 1;

			for( my $i=0 ; $i<scalar(@f) ; $i++ ) {
				$f[$i] =~ s/\d+://g;
			}
		}

		push(@class, $c);
		push(@{$data[$cnt++]}, @f);
	}

	print STDERR "# memory loading done.\n";

	my (@avg, @var, @threshold) = ();
	for( my $i=0 ; $i<scalar(@sum) ; $i++ ) {
		$avg[$i] = $sum[$i] / scalar(@data);

		for( my $j=0 ; $j<scalar(@data) ; $j++ ) {
			$var[$i] += abs($avg[$i] - $data[$j][$i])**2;
		}
		$var[$i] = $var[$i]/scalar(@data);		
		$var[$i] = sqrt($var[$i]);

		$threshold[$i] = abs($avg[$i] + $args{"c"} * $var[$i]);
	}

	my (@result) = cutoff_features(\@data, \@threshold, \@class, $svm_form);

	print join("\n", @result)."\n";
}
#====================================================================
# sub functions
#====================================================================
sub cutoff_features {
	my (@data) 		= (@{shift(@_)});
	my (@threshold) = (@{shift(@_)});
	my (@class) 	= (@{shift(@_)});
	my $svm_form 	= shift(@_);

	my (@ret) = ();

	my $ignore = 0;
	for( my $i=0 ; $i<scalar(@data) ; $i++ ) {
		my $flag = 1;
		for( my $j=0 ; $j<scalar(@threshold) ; $j++ ) {		
			next if( abs($data[$i][$j]) < $threshold[$j] );

			# print STDERR "#>> $i:$j \t ".abs($data[$i][$j])." > $threshold[$j]\n";
			$flag = 0;
			last;
		}

		if( $flag == 1 ) {
			if( $svm_form == 1 ) {
				my (@buf) = (@{$data[$i]});
				for( my $j=0 ; $j<scalar(@buf) ; $j++ ) {
					$buf[$j] = sprintf("%d:%s", $j+1, $buf[$j]);
				}
				push(@ret, sprintf("%s\t%s", $class[$i], join("\t", @buf)));
			} else {
				push(@ret, sprintf("%s\t%s", $class[$i], join("\t", @{$data[$i]})));
			}
		} else {
			$ignore++;
			# printf STDERR "# OUT: %s\t%s\n", $class[$i], join("\t", @{$data[$i]});
		}
	}

	my $rate = ( $ignore > 0 ) ? $ignore / scalar(@data) : 0;
	printf STDERR "# ignore : %d / %d (%f)\n", $ignore, scalar(@data), $rate;

	return (@ret);
}
#====================================================================
__END__

