#!/usr/bin/perl
#====================================================================
use strict;
use Encode;
use FileHandle;
use File::Path;
use IPC::Open2;
use PerlIO::gzip;
use Getopt::Long;
#====================================================================
my (%args) = (	
);

GetOptions(
	"diff" => \$args{"diff"},
	"debug" => \$args{"debug"},
);
#====================================================================
# MAIN
#====================================================================
main: {
	MergeColumn(@ARGV);	
}
#====================================================================
# sub functions
#====================================================================
sub MergeColumn
{
	my (@file_list) = @_;

	my $col=0;

	print STDERR "# Merge column:\n";

	my (@col_count) = ();
	my (%data_index) = ();
	my (%columns, %uniq) = ();
	foreach my $fn ( @file_list ) {
		$fn =~ s/^\'|\'$//g;
		$fn =~ s/^\"|\"$//g;

		print STDERR "# $fn\n";

		next if( !-e $fn );

		die "can not open : $fn $!\n" unless( open(FILE, $fn) );

		my $row = 0;
		foreach my $str ( <FILE> ) {
			$str =~ s/\r?\n$//;	
			$str =~ s/\s+$//;	

			$row++;

			my (@t) = split(/\t/, $str);

			$col_count[$col] = scalar(@t) if( $col_count[$col] < scalar(@t) );

			if( !defined($uniq{$t[0]}[$col]) && $uniq{$t[0]}[$col] != 1 ) {
				$columns{$t[0]}++;
				$uniq{$t[0]}[$col] = 1;
			}
			$data_index{$t[0]}[$col] = $str;
		}

		$col++;
		
		close(FILE);
	}

	print STDERR "\n\n";

	foreach my $col ( keys %columns ) {
		printf STDERR "%d\t%s\t%s\n", $columns{$col}, $col, join("\t", @{$data_index{$col}}) if( $args{"debug"} );

		if( $args{"diff"} ) {
			next if( $columns{$col} > scalar(@file_list) );
		} else {
			next if( $columns{$col} < scalar(@file_list) );
		}

		for( my $i=0 ; $i<scalar(@file_list) ; $i++ ) {
			next if( defined($data_index{$col}[$i]) );

			$data_index{$col}[$i] = "";
			foreach( 0..($col_count[$i]-2) ) {
				$data_index{$col}[$i] .= "\t";
			}
		}

		print join("\t", @{$data_index{$col}})."\n";
	}
}
#====================================================================
__END__


sort -R --random-source=/dev/urandom 


