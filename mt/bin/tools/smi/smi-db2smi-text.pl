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
	"max_core" => 12,
	"i" => 0
);

GetOptions(
	"i=i" => \$args{"i"},
	"db=s" => \$args{"db"},
	"id=s" => \$args{"id"},

	"max_core=i" => \$args{"max_core"},
	"uniq_text_db=s" => \$args{"uniq_text_db"},

	"raw_text" => \$args{"raw_text"},
	"raw|raw_smi" => \$args{"raw_smi"},
	
	"debug" => \$args{"debug"},
);


main: {
	binmode(STDIN, ":utf8");
	binmode(STDOUT, ":utf8");
	binmode(STDERR, ":utf8");

	# open database
	my $dbh = open_smi_db($args{"db"});

	my (@where) = ();
	if ( defined($args{"id"})  ) {
		push(@where, sprintf("id = %s", $args{"id"})) if ( defined($args{"id"}) );
    } else {
		push(@where, sprintf("id %% %d=%d", $args{"max_core"}, $args{"i"}));
	}
    
	my $query = sprintf("SELECT id, smi FROM smi WHERE %s", join(" AND ", @where));

    my $sth = $dbh->prepare($query);
    $sth->execute;

	my $dbh_uniq = open_smi_db($args{"uniq_text_db"});
	
	# create table
	$query = qq(
CREATE TABLE IF NOT EXISTS smi_text (
  id INTEGER PRIMARY KEY AUTOINCREMENT, 
  smi_text TEXT NOT NULL UNIQUE,
  uniq_ko TEXT NOT NULL UNIQUE,
  uniq_en TEXT NOT NULL UNIQUE
);
	);
	$dbh_uniq->do($query);
    
	my $cnt = 0;
	while( my $row=$sth->fetchrow_hashref ) {
		my (@data) = smi_to_text($row->{"smi"});

		my (@new_data) = ();

		if( $args{"raw_text"} ) {
			my (@buf) = get_smi_text_to_list(\@data);
			print join("\n", @buf);
        }
        
		merge_overlap(\@data);
		merge_sentence(\@data); 
		merge_empty(\@data);

		split_sentence(\@data);
		split_dash(\@data, "no dash"); 

		next if( scalar(@data) < 20 );

		my (@smi_text, @text_ko, @text_en) = (); 
		get_smi_text_to_list(\@data, \@smi_text, \@text_ko, \@text_en);
		print join("\n", @smi_text);
		
		$dbh_uniq->do('INSERT INTO smi_text (id, smi_text, uniq_ko, uniq_en) VALUES (?, ?, ?, ?)', undef, 
					$row->{"id"}, join("\n", @smi_text), join("\n", @text_ko), join("\n", @text_en));
		
		if( defined($dbh->errstr) ) {
			print STDERR "ERROR: ", $dbh_uniq->errstr, ", query: ", $query, "\n";
		}

		$cnt++;
		print STDERR "\r($cnt)";	
	}
	
	$dbh_uniq->disconnect();

	$dbh->disconnect();
}


__END__
