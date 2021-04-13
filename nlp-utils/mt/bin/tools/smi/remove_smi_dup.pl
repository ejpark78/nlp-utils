#!/usr/bin/perl
#====================================================================
use strict;
use utf8;
use Encode;
use FileHandle;
use File::Path;
use Getopt::Long;
use Tie::LevelDB; 
use POSIX;
#====================================================================
my (%args) = (
);

GetOptions(
	"fn=s" => \$args{"fn"},
	"iter=i" => \$args{"iter"},
);
#====================================================================
# MAIN
#====================================================================
main: {
	binmode(STDIN, ":utf8");
	binmode(STDOUT, ":utf8");
	binmode(STDERR, ":utf8");

	my $cnt_smi = 0;
	my $prev_fn = "";
	my $domain = "";

	my (@one_smi, @index) = ();
	foreach my $line ( <STDIN> ) {
		$line =~ s/^\s+|\s+$//g;

		my ($fn, $timeline, $smi) = split(/\t/, $line, 3); # en-ko
		# my ($fn, $timeline, $smi) = split(/\t/, $line, 4); # en only

		my ($t) = split(/ \~ /, $timeline);

		if( $prev_fn eq "" ) {
			$prev_fn = $fn;
			$domain = get_domain($fn);
		}

		if( $prev_fn eq $fn ) {
			$one_smi[$cnt_smi]{$smi} = 1;
			push(@{$index[$cnt_smi]}, $domain."\t".$line);
		} else {
			$cnt_smi++;
			$domain = get_domain($fn);
		}

		$prev_fn = $fn;
	}

	my (%dup) = ();
	for( my $i=0 ; $i<$cnt_smi ; $i++ ) {
		next if( defined($dup{$i}) );

		my $cnt_a = scalar keys %{$one_smi[$i]};

		for( my $j=$i+1 ; $j<$cnt_smi ; $j++ ) {
			my $cnt_b = scalar keys %{$one_smi[$j]};
			
			next if( abs($cnt_a - $cnt_b) > 20 );

			my $cnt = 0;
			foreach my $str ( keys %{$one_smi[$i]} ) {
				$cnt++ if( defined($one_smi[$j]{$str}) );
				# print $str,"\n";
			}

			if( abs($cnt_a - $cnt) < 20 ) {
				printf STDERR "%d-%d\t%d:%d\t%d\n", $i, $j, $cnt_a, $cnt_b, $cnt;
				$dup{$j} = 1;
			}
		}
	}

	for( my $i=0 ; $i<$cnt_smi ; $i++ ) {
		next if( defined($dup{$i}) );

		foreach my $line ( @{$index[$i]} ) {
			printf "%s\n", $line;
		}
	}
}
#====================================================================
# sub functions
sub get_domain {
	my $fn = shift(@_);

	my $ret = "drama";

	return $ret if $fn =~ m/Season/i;
	return $ret if $fn =~ m/Ep\d*/i;
	return $ret if $fn =~ m/Episode/i;
	return $ret if $fn =~ m/시즌.+$/i;
	return $ret if $fn =~ m/\d+x\d+/i;
	return $ret if $fn =~ m/s\d+x\d+/i;
	return $ret if $fn =~ m/s\d+e/i;
	return $ret if $fn =~ m/s\d+\s*e\d+/i;
	return $ret if $fn =~ m/\d+편/i;

	return "movies";
}
#====================================================================
#Replace a string without using RegExp.
sub str_replace {
	my $replace_this = shift;
	my $with_this  = shift; 
	my $string   = shift;
	
	my $length = length($string);
	my $target = length($replace_this);
	
	for(my $i=0; $i<$length - $target + 1; $i++) {
		if(substr($string,$i,$target) eq $replace_this) {
			$string = substr($string,0,$i) . $with_this . substr($string,$i+$target);
			return $string; #Comment this if you what a global replace
		}
	}
	return $string;
}
#====================================================================
sub get_ngram
{
	my (@token) = (@{shift(@_)});
	my $n = shift(@_);
	my $ret = shift(@_);

	$n--;

	for( my $i=0 ; $i<scalar(@token)-$n ; $i++ ) {
		my $buf = join(" ", @token[$i..($i+$n)]);

		$buf =~ s/\s+$//;
		$buf =~ s/\s+/ /g;

		next if( $buf eq "" );

		push(@{$ret}, $buf);
	}
}
#====================================================================
# sub max { $_[$_[0] < $_[1]] }
# sub min { $_[$_[0] > $_[1]] }
#====================================================================
sub comma {
	my $cnt = shift(@_);

	$cnt = reverse join ",", (reverse $cnt) =~ /(\d{1,3})/g;

	return $cnt;
}
#====================================================================
__END__


