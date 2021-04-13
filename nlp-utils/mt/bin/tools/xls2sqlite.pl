#!/usr/bin/perl
#====================================================================
use strict;
use utf8;

use DBI;

use Encode;
use Spreadsheet::ParseExcel;
use Getopt::Long;
#====================================================================
binmode(STDIN, ":utf8");
binmode(STDOUT, ":utf8");
binmode(STDERR, ":utf8");
#====================================================================
my (%args) = ();

GetOptions(
	"fn=s" => \$args{"fn"},
	"out=s" => \$args{"out"},
	"sheet_name=s" => \$args{"sheet_name"},
	"debug" => \$args{"debug"}
);
#====================================================================
main: {
	# set out file name
	if( !defined($args{"out"}) ) {
		$args{"out"} = $args{"fn"};
		$args{"out"} =~ s/\..+?$/\.sqlite3/;
	}

	# check out file exists
	if( -e $args{"out"} ) {
#		print "ERROR: ".$args{"out"}." is already exists...\n";
#		exit(1);
	}

	print "FN: ".$args{"fn"}." => ".$args{"out"}."\n";
	print "\n";

	# open excel file
	my $xls = new Spreadsheet::ParseExcel;
	my $book = $xls->Parse($args{"fn"}) or die "Could not open source Excel file ".$args{"fn"}.": ".$!;

	# open database
	my $dbh = DBI->connect("dbi:SQLite:dbname=".$args{"out"}, "", "", {AutoCommit => 1, PrintError => 1});

	# Maximise compatibility
	$dbh->do('PRAGMA legacy_file_format = 1');

	# Turn on all the go-faster pragmas
	$dbh->do('PRAGMA synchronous  = 0');
	$dbh->do('PRAGMA temp_store   = 2');
	$dbh->do('PRAGMA journal_mode = OFF');
	$dbh->do('PRAGMA locking_mode = EXCLUSIVE');

	foreach my $sheet_number (0 .. $book->{SheetCount}-1) {
		my $sheet = $book->{Worksheet}[$sheet_number];

		my $table_name = $sheet->{Name};

		next if( defined($args{"sheet_name"}) && $args{"sheet_name"} ne $table_name );
		print "Table Name: $table_name\n";

		# sanity checking on the source file: rows and columns should be sensible
		next unless defined $sheet->{MaxRow};
		next unless $sheet->{MinRow} <= $sheet->{MaxRow};

		next unless defined $sheet->{MaxCol};
		next unless $sheet->{MinCol} <= $sheet->{MaxCol};

		# rows
		my (@rows) = get_sheet_rows($sheet);

		my (@title1) = @{shift(@rows)};
		my (@title2) = @{shift(@rows)};
		my (@title3) = @{shift(@rows)}; # type INTEGER, STRING, DATE

		print "Column #1: ".join("\t", @title1)."\n";
		print "Column #2: ".join("\t", @title2)."\n";
		print "Column #3: ".join("\t", @title3)."\n";
		print "\n";

		my (%column_mapping, @column_list, @create_value) = ();
		for( my $i=0 ; $i<scalar(@title1) ; $i++ ) {
			if( !defined($column_mapping{$title1[$i]}) ) {
				push(@column_list, $title1[$i]);
				
				if( $title3[$i] ne "TEXT" && $title3[$i] ne "INT" && $title3[$i] ne "REAL" ) {
					$title3[$i] = "TEXT";
				}

				push(@create_value, "'".$title1[$i]."' ".$title3[$i]);
			}
			$column_mapping{$title1[$i]}{$title2[$i]} = $title1[$i];
		}

		# make column_list string
		my (@column_list_quote) = ();
		foreach my $col ( @column_list ) {
			push(@column_list_quote, "'$col'");
		}

		my $query = "";

		# drop table
		$query = "DROP TABLE IF EXISTS $table_name";
		$dbh->do($query);

		# create table
		$query = "CREATE TABLE $table_name (".join(",", @create_value).")";
		$dbh->do($query);

	    if( $dbh->errstr ne "" ) {
	    	print STDOUT "$query\n";
	    }

	    my $idx_cnt = 0;
		foreach my $row ( @rows ) {
			my (@list) = (@{$row});

			my (%one_row) = ();
			for( my $i=0 ; $i<scalar(@list) ; $i++ ) {
				my $alias = $title1[$i];
				my $tag   = $title2[$i];
				my $value = $list[$i];

				if( scalar( keys( %{$column_mapping{$alias}} ) ) > 1 ) {
					$value = "<$tag>$value</$tag>";
				}

				if( !defined($one_row{$alias}) ) {
					$one_row{$alias} = "";
				}
				$one_row{$alias} .= $value;
			}

			# get vals
			my (@vals) = ();
			foreach my $column ( @column_list ) {
				my $val = $one_row{$column};
				$val =~ s/^\'\=/\=/;
				$val =~ s/\'/\'\'/g;
				
				$val =~ s/^\s+|\s+$//g;				

				if( $column eq "_idx" && $val eq "" ) {
					$val = ++$idx_cnt;
				}

				push(@vals, $val);
			}

			$query = "REPLACE INTO $table_name (".join(",", @column_list_quote).") VALUES ('".join("', '", @vals)."')";
		    $dbh->do($query);

		    if( $dbh->errstr ne "" ) {
		    	print STDOUT "$query\n";
		    }
		}

		# drop index table
		$query = "DROP INDEX IF EXISTS ".$table_name."_idx";
		$dbh->do($query);

		# create index table
		$query = "CREATE INDEX ".$table_name."_idx ON ".$table_name." (".join(",", @column_list_quote).")";
		$dbh->do($query);

	    if( $dbh->errstr ne "" ) {
	    	print STDOUT "$query\n";
	    }
	}

    $dbh->disconnect();
}
#====================================================================
sub get_sheet_rows {
	my $sheet = shift(@_);

	my (@rows) = ();

	my $prev_row_index = 0;
	foreach my $row_index ( $sheet->{MinRow} .. $sheet->{MaxRow} ) {
		my (@buf) = ();
		foreach my $col_index ($sheet->{MinCol} .. $sheet->{MaxCol}) {
			my $source_cell = $sheet->{Cells}[$row_index][$col_index];
			if( $source_cell ) {
				push(@buf, $source_cell->Value);
			} else {
				push(@buf, "");
			}
		}

		push(@rows, \@buf);
	}

	return @rows;
}
#====================================================================
__END__

