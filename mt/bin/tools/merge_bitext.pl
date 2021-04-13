#!/usr/bin/perl
#====================================================================
use strict;
use Encode;
use FileHandle;
use File::Path;
use Getopt::Long;
#====================================================================
my (%args) = (	
);

GetOptions(
	'a=s' => \$args{"a"}, 	
	'b=s' => \$args{"b"}
);
#====================================================================
# MAIN
#====================================================================
main: {
	MergeBitext($args{"a"}, $args{"b"});	
}
#====================================================================
# sub functions
#====================================================================
sub ReadBitext {
	my $fn = shift(@_);
	my $ret = shift(@_);
	my $reverse = shift(@_);

	die "can not open : $fn $!\n" unless( open(FILE, $fn) );

	foreach my $str ( <FILE> ) {
		$str =~ s/\r?\n$//;	

		my ($a, $b) = split(/\t/, $str, 2);

		if( $reverse ) {
			($a, $b) = ($b, $a);
		}

		if( !defined($ret->{$a}{$b}) ) {
			$ret->{$a}{$b} = 0;
		}

		$ret->{$a}{$b}++;
	}	
	
	close(FILE);
}
#====================================================================
sub MergeBitext {
	my ($_a, $_b) = @_;

	my (%file_a, %file_b) = ();

	ReadBitext($_a, \%file_a, 0);
	ReadBitext($_b, \%file_b, 0);

	foreach my $b ( keys %file_b ) {
		next if( !defined($file_a{$b}) );

		my ($a) = (keys %{$file_a{$b}});
		my ($c) = (keys %{$file_b{$b}});
		print "$a\t$b\t$c\n";
	}
}
#====================================================================
__END__

