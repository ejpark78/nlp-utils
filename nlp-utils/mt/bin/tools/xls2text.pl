#!/usr/bin/perl
#====================================================================
use strict;
use utf8;

use Encode;

use Spreadsheet::ParseExcel;
use Spreadsheet::WriteExcel;

use Getopt::Long;
#====================================================================
binmode(STDIN, ":utf8");
binmode(STDOUT, ":utf8");
binmode(STDERR, ":utf8");
#====================================================================
my (%args) = ();

GetOptions(
	'euc-kr' => \$args{"euc-kr"},
	'out=s' => \$args{"out"},
	'stdout' => \$args{"stdout"},
	'decode_fn' => \$args{"decode_fn"},
);
#====================================================================
if (!@ARGV) {
    @ARGV = <STDIN>;
    chop(@ARGV);
}

foreach my $fn ( @ARGV ) {
	$fn =~ s/\s+$//;
	$fn =~ s/\*$//;

	# print STDERR "fn: $fn\n";
	if( $args{"decode_fn"} ) {
		$fn = decode("utf8", $fn);
	}

	print STDERR "in:: ".$fn."\n";
	
	if( $fn =~ /\.xlsx/ ) {
		Xlsx2Text($fn, $args{"stdout"}, $args{"out"});
	} else {
		Excel2Text($fn, $args{"stdout"}, $args{"out"});
	}
	
	print "\n";
}
#====================================================================
sub Xlsx2Text 
{
	my ($sourcename, $_stdout, $_out) = @_;

	use Spreadsheet::XLSX;

	my $excel = Spreadsheet::XLSX->new($sourcename);

	my $buf = "";

	foreach my $sheet ( @{$excel->{"Worksheet"}} ) {
		print STDERR "sheet: $sheet\n";

		$sheet->{"MaxRow"} ||= $sheet->{"MinRow"};

		my $prev_row_index = 0;
		foreach my $row ( $sheet->{"MinRow"}..$sheet->{"MaxRow"} ) {
			$sheet->{"MaxCol"} ||= $sheet->{"MinCol"};

			foreach my $col ( $sheet->{"MinCol"}..$sheet->{"MaxCol"} ) {
				my $cell = $sheet->{"Cells"}[$row][$col];

				if ($cell) {
					my $line = $cell->{"Val"};
					$line = decode("utf8", $line);

					# printf("( %s , %s ) => %s\n", $row, $col, $line);
					$prev_row_index = $row;
					
					$line =~ s/\t+/<tab>/g;
					$line =~ s/\n/<br>/g;
					$line =~ s/\s+/ /g;
					$line =~ s/’/'/g;					
					$line =~ s/^\s+|\s+$//g;
					
					$buf .= $line."\t";	
				} else {
					$buf .= "\t";	
				}
			}

			$buf .= "\n";	
		}

		# my $fn = $sourcename.".".$sheet->{"Name"}.".txt";		
		my $fn = $sourcename.".".decode("utf8", $sheet->{"Name"}).".txt";		

		# $fn = encode("utf8", $fn);
		# $fn = decode("utf8", $fn);

		if( defined($_out) ) {
			$fn = $_out;
		}

		if( defined($_stdout) ) {		
			print $buf;
		} else {
			print STDERR "out:: ".$fn."\n";

			unless( open(FILE_OUT, ">", $fn) ) {die "can not open ".$fn.": ".$!."\n";}

			if( $args{"euc-kr"} ) {
				binmode(FILE_OUT, ":encoding(euc-kr)");
			} else {
				binmode(FILE_OUT, ":utf8");
			}
			
			print FILE_OUT $buf;
			
			close(FILE_OUT);
		}
		
		$buf = "";
	}	
}
#====================================================================
sub Excel2Text
{
	my ($sourcename, $_stdout, $_out) = @_;

	my $source_excel = new Spreadsheet::ParseExcel;
	my $source_book = $source_excel->Parse($sourcename) or die "Could not open source Excel file ".$sourcename.": ".$!;
	
	my $buf = "";
	
	foreach my $source_sheet_number (0 .. $source_book->{"SheetCount"}-1) {
		my $source_sheet = $source_book->{"Worksheet"}[$source_sheet_number];
		
		# sanity checking on the source file: rows and columns should be sensible
		next unless defined $source_sheet->{"MaxRow"};
		next unless $source_sheet->{"MinRow"} <= $source_sheet->{"MaxRow"};
		
		next unless defined $source_sheet->{"MaxCol"};
		next unless $source_sheet->{"MinCol"} <= $source_sheet->{"MaxCol"};
		
		my $prev_row_index = 0;
		foreach my $row_index ( $source_sheet->{"MinRow"}..$source_sheet->{"MaxRow"} ) {
			foreach my $col_index ( $source_sheet->{"MinCol"}..$source_sheet->{"MaxCol"} ) {
				my $source_cell = $source_sheet->{"Cells"}[$row_index][$col_index];
				if( $source_cell ) {
					$prev_row_index = $row_index;
					
					my $line = $source_cell->Value;
					
					$line =~ s/\t+/<tab>/g;
					$line =~ s/\n/<br>/g;
					$line =~ s/\s+/ /g;
					$line =~ s/’/'/g;					
					$line =~ s/^\s+|\s+$//g;
					
					$buf .= $line."\t";	
				} else {
					$buf .= "\t";	
				}
			} 
			$buf .= "\n";	
		} 

		# wrate file
		# my $fn = $sourcename.".".$source_sheet->{"Name"}.".txt";		
		my $sub_fn = $source_sheet->{"Name"};
		print $sourcename.".".$sub_fn."\n";

		my $fn = $sourcename.".".$sub_fn.".txt";		
		if( defined($_out) ) {
			$fn = $_out;
		}

		if( defined($_stdout) ) {		
			print $buf;
		} else {
			print STDERR "out:: ".$fn."\n";

			unless( open(FILE_OUT, ">", $fn) ) {die "can not open ".$fn.": ".$!."\n";}

			if( $args{"euc-kr"} ) {
				binmode(FILE_OUT, ":encoding(euc-kr)");
			} else {
				binmode(FILE_OUT, ":utf8");
			}
			
			print FILE_OUT $buf;
			
			close(FILE_OUT);
		}
		
		$buf = "";
	} 
	
	return $buf."\n\n";
}
#====================================================================
__END__


http://www.ibm.com/developerworks/linux/library/l-pexcel/

ppm> install OLE::Storage_Lite
ppm> install Spreadsheet::ParseExcel
ppm> install Spreadsheet::WriteExcel


