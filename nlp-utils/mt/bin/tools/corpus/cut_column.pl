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
	"f" => "tm-2M:bleu",
);

GetOptions(
	"f=s" => \$args{"f"},
	"debug" => \$args{"debug"}
);
#====================================================================
# MAIN
#====================================================================
main: {
	binmode(STDIN, "utf8");
	binmode(STDOUT, "utf8");
	binmode(STDERR, "utf8");

	my $flag = 0;
	my (%title) = ();

	printf STDERR "f: %s\n", $args{"f"};

	my (@f_list) = split(/,/, $args{"f"});

	while( my $line = <STDIN> ) {
		$line =~ s/\s+$//;

		next if( $line eq "" );

		my (@t) = split(/\t/, $line);

		if( $flag == 0 ) {
			for( my $i=0 ; $i<scalar(@t) ; $i++ ) {
				print $t[$i], "\t", $i, "\n";
				$title{$t[$i]} = $i;
			}

			$flag = 1;
		}

		my (@row) = ();
		foreach my $col_name ( @f_list ) {
			push(@row, $t[$title{$col_name}]);
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

