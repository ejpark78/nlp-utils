#!/usr/bin/perl -w

use strict;
use utf8;
use DBI;
use Getopt::Long;

use lib "$ENV{TOOLS}";
require "base_lib.pm";


my (%args) = (
);

GetOptions(
	# run option
	'o|out=s' => \$args{"out"},
	'table=s' => \$args{"table"},
	'header=s' => \$args{"header"},
	'schema=s' => \$args{"schema"},
);


main: {
	binmode(STDIN, ":utf8");
	binmode(STDOUT, ":utf8");
	binmode(STDERR, ":utf8");

	# check out file exists
	if( !defined($args{"out"}) || !defined($args{"table"}) || (!defined($args{"header"}) && !defined($args{"schema"})) ) {
		print STDERR "Usage: -o <sqlite out> -table <table name> -header <table column name> -schema <schema info>\n";
		exit(1);
	}
	
	print "FN: => ".$args{"out"}."\n\n";
	
	# open database
	my $dbh = open_smi_db($args{"out"});

	my (@header, @cols) = ();
	if( $args{"schema"} ) {
		foreach my $col ( split(/,/, $args{"schema"}) ) {
			push(@cols, "?");
			push(@header, "$col");
		}
	} elsif( $args{"header"} ) {
		foreach my $col ( split(/,/, $args{"header"}) ) {
			push(@cols, "?");
			push(@header, "$col TEXT");
		}
	}

	my $table = $args{"table"};
	my $query = "CREATE TABLE IF NOT EXISTS '$table' (".join(",", @header).");";

	$dbh->do($query);
	print STDOUT "ERROR: ", $dbh->errstr, ", query:", $query, "\n" if( defined($dbh->errstr) );

	my $i = 0;
	foreach my $line ( <STDIN> ) {
		$line =~ s/\s+$//;
		my (@values) = split(/\t/, $line);

		if( scalar(@cols) != scalar(@values) ) {
			printf STDERR "ERROR mismatch col & values counts: %d != %d\n", scalar(@cols), scalar(@values);
			exit(1);
		}

		my $query = "INSERT INTO '$table' VALUES (".join(", ", @cols).")";
		$dbh->do($query, undef, @values);		
	
		if( defined($dbh->errstr) ) {
			printf STDOUT "ERROR: %s, query: %s, values: %s\n", $dbh->errstr, $query, join("\t", @values);
		}

		if( ($i++ % 2000) == 0 ) {
			printf STDERR "loading: (%s)\t\t\t\r", comma($i);
		}					
	}

	$dbh->disconnect();
}


sub open_smi_db {
	my $db_name = shift(@_);
	
	# to use if( defined($dbh->errstr) ): PrintError => 0, RaiseError => 0
	my $dbh = DBI->connect("DBI:SQLite:dbname=".$db_name, "", "",
						   {AutoCommit => 1, PrintError => 0, RaiseError => 0});

	# Maximise compatibility
	$dbh->do('PRAGMA legacy_file_format = 1');

	# Turn on all the go-faster pragmas
	$dbh->do('PRAGMA synchronous  = 0');
	$dbh->do('PRAGMA temp_store   = 2');
	$dbh->do('PRAGMA journal_mode = OFF');
	$dbh->do('PRAGMA locking_mode = EXCLUSIVE');
	
	return $dbh;
}


__END__


