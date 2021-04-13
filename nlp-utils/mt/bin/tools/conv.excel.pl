#!/usr/bin/perl
#====================================================================
use strict;
use utf8;

use Encode;

use Spreadsheet::ParseExcel;
use Spreadsheet::WriteExcel;

#use Spreadsheet::Read;
use Getopt::Long;
#====================================================================
binmode(STDIN, ":utf8");
binmode(STDOUT, ":utf8");
binmode(STDERR, ":utf8");
#====================================================================
my (%args) = ();

GetOptions(
	'stdout' => \$args{stdout},
);
#====================================================================
if (!@ARGV) {
    @ARGV = <STDIN>;
    chop(@ARGV);
}

foreach my $fn ( @ARGV ) {
	$fn =~ s/\s+$//;
	$fn =~ s/\*$//;

	print STDERR "in:: ".$fn."\n";
	
	if( $fn =~ /\.xlsx/ ) {
#		Excel2Text2($fn);
	} else {
		Excel2Text($fn, $args{stdout});
	}
	
	print "\n";
}

#close(PIPE);
#====================================================================
sub Excel2Text2
{
#	my ($sourcename) = @_;
#
#	return;
#
#	my $xls = ReadData ($sourcename);
# 
#	for my $cell (map { "A$_" } 1 .. 100) {
#	$_ = $xls->[1]{$cell};
#	
#	if (/test/) {
#	print "found \"test\" in cell: $cell\n";
#	}
#	}
}
#====================================================================
sub Excel2Text
{
	my ($sourcename, $_stdout) = @_;

	my $source_excel = new Spreadsheet::ParseExcel;
	my $source_book = $source_excel->Parse($sourcename) or die "Could not open source Excel file ".$sourcename.": ".$!;
	
	my $buf = "";
	
	foreach my $source_sheet_number (0 .. $source_book->{SheetCount}-1) {
		my $source_sheet = $source_book->{Worksheet}[$source_sheet_number];
		
		# sanity checking on the source file: rows and columns should be sensible
		next unless defined $source_sheet->{MaxRow};
		next unless $source_sheet->{MinRow} <= $source_sheet->{MaxRow};
		
		next unless defined $source_sheet->{MaxCol};
		next unless $source_sheet->{MinCol} <= $source_sheet->{MaxCol};
		
		my $prev_row_index = 0;
		foreach my $row_index ($source_sheet->{MinRow} .. $source_sheet->{MaxRow}) {
			foreach my $col_index ($source_sheet->{MinCol} .. $source_sheet->{MaxCol}) {
				my $source_cell = $source_sheet->{Cells}[$row_index][$col_index];
				if( $source_cell ) {
					$prev_row_index = $row_index;
					
					my $line = $source_cell->Value;
					
					$line =~ s/\t+/ /g;
					$line =~ s/\s+/ /g;
					$line =~ s/^\s+|\s+$//g;
					$line =~ s/\n/ /g;
					
#					$line =~ s/\"/\"\"/g;
				
					$buf .= $line."\t";	
#					print $line."\t";
#					print "\"".$line."\",";
				} else {
					$buf .= "\t";	
#					print "\t";	
#					print ",";	
				}
			} 
			$buf .= "\n";	
#			print "\n";	
		} 
		my $fn = $sourcename.".".$source_sheet->{Name}.".txt";
		
		if( defined($_stdout) ) {		
			print $buf;
		} else {
			print STDERR "out:: ".$fn."\n";

			unless( open(FILE_OUT, ">", $fn) ) {die "can not open ".$fn.": ".$!."\n";}
			binmode(FILE_OUT, ":utf8");
			
			print FILE_OUT $buf;
			
			close(FILE_OUT);
		}
		
		$buf = "";
	} 
	
#	print "\n\n";
	
	return $buf."\n\n";
}
#====================================================================
__END__


http://www.ibm.com/developerworks/linux/library/l-pexcel/

ppm> install OLE::Storage_Lite
ppm> install Spreadsheet::ParseExcel
ppm> install Spreadsheet::WriteExcel


