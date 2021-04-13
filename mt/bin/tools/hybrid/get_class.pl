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
	"seq|sequence=s" => \$args{"sequence"},

	"smt-bleu=f" => \$args{"smt-bleu"},
	"smt-nist=f" => \$args{"smt-nist"},
	"smt-meteor=f" => \$args{"smt-meteor"},

	"lbmt-bleu=f" => \$args{"lbmt-bleu"},
	"lbmt-nist=f" => \$args{"lbmt-nist"},

	"rank=s" => \$args{"rank"},

	"test" => \$args{"test"},
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

	my (%cnt) = ();
	while( my $line = <STDIN> ) {
		$line =~ s/\s+$//;

		next if( $line eq "" );

		my (@t) = split(/\t/, $line);

		my $class = "smt";

		if( !$param{"test"} ) {
			if( defined($param{"rank"}) ) {
				if( $param{"rank"} eq "meteor" ) {
					$class = "lbmt" if( $t[$seq{"lbmt-meteor"}] > $t[$seq{"smt-meteor"}] );
				}

				if( $param{"rank"} eq "r-meteor" ) {
					$class = "lbmt" if( $t[$seq{"lbmt-meteor"}] < $t[$seq{"smt-meteor"}] );
				}

				if( $param{"rank"} eq "meteor-bleu" ) {
					$class = "lbmt" if( $t[$seq{"lbmt-meteor"}] > $t[$seq{"smt-meteor"}] );
					$class = "lbmt" if( $t[$seq{"lbmt-bleu"}] > $t[$seq{"smt-bleu"}] );
				}

				if( $param{"rank"} eq "meteor-nist" ) {
					$class = "lbmt" if( $t[$seq{"lbmt-meteor"}] > $t[$seq{"smt-meteor"}] );
					$class = "lbmt" if( $t[$seq{"lbmt-nist"}] > $t[$seq{"smt-nist"}] );
				}

				if( $param{"rank"} eq "nist" ) {
					$class = "lbmt" if( $t[$seq{"lbmt-nist"}] > $t[$seq{"smt-nist"}] );
				}

				if( $param{"rank"} eq "bleu" ) {
					$class = "lbmt" if( $t[$seq{"lbmt-bleu"}] > $t[$seq{"smt-bleu"}] );
				}

				if( $param{"rank"} eq "both" ) {
					$class = "lbmt" if( $t[$seq{"lbmt-bleu"}] > $t[$seq{"smt-bleu"}] && $t[$seq{"lbmt-nist"}] > $t[$seq{"smt-nist"}] );
				}

				if( $param{"rank"} eq "nist-bleu" ) {
					$class = "lbmt" if( $t[$seq{"lbmt-nist"}] > $t[$seq{"smt-nist"}] );
					$class = "lbmt" if( $t[$seq{"lbmt-bleu"}] > $t[$seq{"smt-bleu"}] );
				}

				if( $param{"rank"} eq "all" ) {
					$class = "lbmt" if( $t[$seq{"lbmt-nist"}] > $t[$seq{"smt-nist"}] );
					$class = "lbmt" if( $t[$seq{"lbmt-bleu"}] > $t[$seq{"smt-bleu"}] );
					$class = "lbmt" if( $t[$seq{"lbmt-bleu"}] > $t[$seq{"smt-bleu"}] && $t[$seq{"lbmt-nist"}] > $t[$seq{"smt-nist"}] );
				}
			}

			if( defined($param{"smt-bleu"}) && $param{"smt-bleu"} >= 0 ) {
				$class = "lbmt" if( $t[$seq{"smt-bleu"}] < $param{"smt-bleu"} );
			}

			if( defined($param{"smt-nist"}) && $param{"smt-nist"} >= 0 ) {
				$class = "lbmt" if( $t[$seq{"smt-nist"}] < $param{"smt-nist"} );
			}

			if( defined($param{"smt-meteor"}) && $param{"smt-meteor"} >= 0 ) {
				$class = "lbmt" if( $t[$seq{"smt-meteor"}] > $param{"smt-meteor"} );
			}
		}

		$cnt{$class}++;

		print "$class\n";
	}

	foreach my $class ( keys %cnt ) {
		print STDERR "# $class\t$cnt{$class}\n";
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

