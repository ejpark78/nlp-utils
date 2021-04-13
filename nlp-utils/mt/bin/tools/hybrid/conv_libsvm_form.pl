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
my (%args) = ();

GetOptions(
	"noclass" => \$args{"noclass"},
	"debug" => \$args{"debug"}
);
#====================================================================
# MAIN
#====================================================================
main: {
	get_class(\%args);	
}
#====================================================================
# sub functions
#====================================================================
sub get_class {
	binmode(STDIN, ":utf8");
	binmode(STDOUT, ":utf8");
	binmode(STDERR, ":utf8");

	my (%param) = (%{shift(@_)});
	my (%seq) = parse_sequence($param{"sequence"});

	# if( $param{"debug"} ) {
		foreach my $k ( keys %param ) {
			print STDERR "# param: $k => ".$param{$k}."\n";
		}
	# }

	while( my $line = <STDIN> ) {
		$line =~ s/\s+$//;

		my (@t) = split(/\t/, $line);

		if( !defined($args{"noclass"}) ) {
			my $class = shift(@t);
			$class = 1 if( $class eq "smt" );
			$class = 0 if( $class eq "lbmt" );
			
			print "$class ";
		} else {
			print "1 ";			
		}

		for( my $i=0 ; $i<scalar(@t) ; $i++ ) {
			printf "%d:%f ", $i+1, $t[$i];
		}

		print "\n";
	}
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

