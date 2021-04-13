#!/usr/bin/perl

use strict;
use Encode;
use PerlIO::gzip;
use Getopt::Long;

use lib "$ENV{TOOLS}";
require "base_lib.pm";


my (%args) = (	
);

GetOptions(
	"header=s" => \$args{"header"},
	"noempty" => \$args{"noempty"}
);


main: {
	MergeFile(@ARGV);	
}


sub MergeFile {
	my (@file_list) = @_;

	my $col=0;

	print STDERR "# * Merge File:\n";

	my (@data, %count) = ();
	foreach my $fn ( @file_list ) {
		$fn =~ s/^\'|\'$//g;
		$fn =~ s/^\"|\"$//g;

		if( !-e $fn ) {
			die "\nERROR: '$fn' is not exists\n";
		}

		my ($open_mode, $file_type) = ("<", `file $fn`);

		$open_mode = "<:gzip" if( $file_type =~ m/ gzip compressed data,/ );
		die "can not open : $fn $!\n" unless( open(FILE, $open_mode, $fn) );

		my $total = get_file_size($fn, $file_type);
		my $start = time();

		my $row = 0;
		foreach my $str ( <FILE> ) {
			$str =~ s/\r?\n$//;	
			$str =~ s/[ ]+$//;	

			$data[$row][$col] = $str;
			$row++;

			$count{$fn}++;

			if( $row % 10000 == 0 ) {
				printf STDERR "# - '$fn' loading: %s   \r", get_progress_str($row, $total, $start);
			}			
		}
		printf STDERR "# - '$fn' loading done: %s     \n", get_progress_str($row, $total, $start);

		$col++;
		
		close(FILE);
	}

	print STDERR "\n\n";

	foreach my $fn ( @file_list ) {
		if( -e $fn ) {
			printf STDERR "# '$fn': %s\n", comma($count{$fn});
		} else {
			printf STDERR "# '$fn' is not exist\n";			
		}
	}

	if( $args{"header"} ) {
		my (@token_header) = split(/,/, $args{"header"});

		print join("\t", @token_header)."\n";
	}

	for( my $i=0 ; $i<scalar(@data) ; $i++ ) {
		my $noempty = 0;
		for( my $j=0 ; $j<scalar(@file_list) ; $j++ ) {
			$data[$i][$j] = "" if( !defined($data[$i][$j]) );
			$data[$i][$j] = "" if( $data[$i][$j] =~ /^\s+$/ );

			if( $data[$i][$j] eq "" && $args{"noempty"} ) {
				$noempty = 1;
				last;
			}
		}

		if( $noempty ) {
			print STDERR "# ERROR: ".join("\t", @{$data[$i]})."\n";
			next;
		}

		print join("\t", @{$data[$i]})."\n";
	}
}


__END__
