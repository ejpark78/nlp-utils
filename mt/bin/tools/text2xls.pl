#!/usr/bin/perl -w
#====================================================================
use strict;

use Getopt::Long;
use POSIX;
use Term::ANSIColor qw(:constants);
use Spreadsheet::WriteExcel;
use Excel::Writer::XLSX;
use Encode;
#====================================================================
my (%args) = (
	"count" => 500000,
	"sheet" => "sheet"
);

GetOptions(
	# run option
	'count=i' => \$args{"count"},
	'o|out=s' => \$args{"out"},
	'header=s' => \$args{"header"},
	'sheet=s' => \$args{"sheet"}
);
#====================================================================
main: {
#	binmode(STDIN, ":utf8");
#	binmode(STDOUT, ":utf8");
#	binmode(STDERR, ":utf8");

	# check out file exists
	if( -e $args{"out"} ) {
		print "ERROR: ".$args{"out"}." is already exists...\n";
		exit(1);
	}
	
	print "FN: => ".$args{"out"}."\n\n";
	
	# create xls
	my $xls = Excel::Writer::XLSX->new($args{"out"});	
	# if( $args{"out"} =~ /\.xlsx/ ) {
	# 	$xls = Excel::Writer::XLSX->new($args{"out"});
	# } else {
	# 	$xls = Spreadsheet::WriteExcel->new($args{"out"});	

	# 	# Create a new Excel workbook
	# 	$xls->set_properties(utf8 => 1);
	# } 

	# create sheet
	my $sheet_num = 1;
	my $sheet;

	if( $args{"count"} > 0 ) {
		$sheet = $xls->add_worksheet(sprintf("%s%d", $args{"sheet"}, $sheet_num));
	} else {
		$sheet = $xls->add_worksheet($args{"sheet"});
	}

	my $header = "";

	my $row = 0;

	if( $args{"header"} ) {
		$header = $args{"header"};
		$header =~ s/,/\t/g;

		insert_line($sheet, $row, $header);
		$row = 1;
	}

	foreach my $line ( <STDIN> ) {
		$line =~ s/\s+$//;
		
		if( $args{"count"} > 0 && $row > $args{"count"} ) {
			$row = 0;

			$sheet_num++;
			$sheet = $xls->add_worksheet(sprintf("%s%d", $args{"sheet"}, $sheet_num));

			insert_line($sheet, $row, $header) if( $header ne "" );
			$row++;
		}

		$header = $line if( $header eq "" );

		insert_line($sheet, $row, $line);
		$row++;
	}
}
#====================================================================
sub insert_line {
	my $sheet = shift(@_);
	my $row = shift(@_);
	my $line = shift(@_);

	# $line =~ s/\|/\t/;
	my (@t) = split(/\t/, $line);

	my $col = 0;
	foreach my $column ( @t ) {
		my $val = decode("utf8", $column);
		$val =~ s/^\=/\'=/g;
		
		$sheet->write($row, $col++, $val);
	}
}
#====================================================================

__END__



