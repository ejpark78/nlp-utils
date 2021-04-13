#!/usr/bin/env perl
#!/usr/bin/perl
#====================================================================
use strict;
use Encode;
use utf8;
use Getopt::Long;
use Data::Printer;
#====================================================================
my (%args) = (
	"d" => "\t",
	"f" => "1,2,3",
);

GetOptions(
	"d=s" => \$args{"d"},
	"f=s" => \$args{"f"},
	"header" => \$args{"header"},
	"debug" => \$args{"debug"}
);
#====================================================================
# MAIN
#====================================================================
main: {
	binmode(STDIN, "utf8");
	binmode(STDOUT, "utf8");
	binmode(STDERR, "utf8");

	my $flag = 1;
	$flag = 0 if( $args{"header"} );

	my (%header) = ();

	# printf STDERR "f: %s\n", $args{"f"};

	my (@f_list) = split(/,/, $args{"f"});

	while( my $line = <STDIN> ) {
		$line =~ s/\s+$//;

		next if( $line eq "" );

		my (@t) = split(/$args{"d"}/, $line);

		my (@row) = ();
		if( $args{"header"} ) {
			if( $flag == 0 ) {
				for( my $i=0 ; $i<scalar(@t) ; $i++ ) {
					print $t[$i], "\t", $i, "\n";
					$header{$t[$i]} = $i;
				}

				$flag = 1;
			}

			foreach my $col_name ( @f_list ) {
				push(@row, $t[$header{$col_name}]);
			}
		} else {
			foreach my $col_name ( @f_list ) {
				push(@row, $t[$col_name-1]) if( defined($t[$col_name-1]) );
			}
		}

		printf "%s\n", join("\t", @row);
	}
}
#====================================================================
#====================================================================
# sub functions
#====================================================================
#====================================================================
__END__

