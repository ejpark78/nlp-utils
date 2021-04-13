#!/usr/bin/perl

use strict;
use utf8;
use Encode;
use Getopt::Long;
use DBI;
use warnings FATAL => 'all';

use FindBin qw($Bin);
use lib "$Bin";
require "smi.pm";

my (%args) = (
	"board_name" => "gomtv"
);

GetOptions(
	"fn=s" => \$args{"fn"},
	"out=s" => \$args{"out"},
	"board=s" => \$args{"board_name"},
);


main: {
	binmode(STDIN, ":utf8");
	binmode(STDOUT, ":utf8");
	binmode(STDERR, ":utf8");
	
	my $board_name = $args{"board_name"};

	my $filename = decode("utf8", $args{"fn"});
	$filename =~ s/^(\.\/)*file\///;

	my (@token) = split(/\//, $filename);

	my $board_id = 0;
	$board_id = $token[-2] if( scalar(@token) > 1 );
	$filename = $token[-1] if( scalar(@token) > 1 );

	# open database
	my $dbh = open_smi_db($args{"out"});

	# create table
	my $query = qq(
CREATE TABLE IF NOT EXISTS smi (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  smi TEXT NOT NULL UNIQUE
);
);

	$dbh->do($query);
	print STDOUT "ERROR: ", $dbh->errstr, ", query:", $query, "\n" if( defined($dbh->errstr) );

	$query = qq(
CREATE TABLE IF NOT EXISTS board (
  name TEXT NOT NULL, 
  id TEXT NOT NULL, 
  filename TEXT NOT NULL,
  PRIMARY KEY (name, id, filename)
);
);

	$dbh->do($query);
	print STDOUT "ERROR: ", $dbh->errstr, ", query:", $query, "\n" if( defined($dbh->errstr) );

	my (@buf) = ();
	while( my $line = <STDIN> ) {
		$line =~ s/^\s+|\s+$//g;
		$line =~ s/[ ]+/ /g;
		
		next if( $line eq "" );

		push(@buf, $line);
	}

	print STDERR "INFO: ", scalar(@buf)."\t$board_name\t$board_id\t$filename\n";
	
	if ( scalar(@buf) > 1 ) {
		$query = "INSERT INTO board (name, id, filename) VALUES (?, ?, ?)";
		$dbh->do($query, undef, $board_name, $board_id, $filename);
		
		if( defined($dbh->errstr) ) {
			print STDERR "ERROR: ", $dbh->errstr, ", query: ", $query, "\n";
		} else {
			$query = "INSERT INTO smi (smi) VALUES (?)";
			$dbh->do($query, undef, join("\n", @buf));
			
			if( defined($dbh->errstr) ) {
				print STDERR "ERROR: ", $dbh->errstr, ", query: ", $query, "\n";
			}
		}
    }

	$dbh->disconnect();

	# $query = "DROP INDEX IF EXISTS ".$table_name."_idx";
	# $query = "CREATE INDEX ".$table_name."_idx ON $table_name (".join(",", @column_list_quote).")";
}

__END__


