#!/usr/bin/perl
#====================================================================
use strict;
use Getopt::Long;
use Tie::LevelDB; 
use Data::Dumper;
use JSON;

use FindBin qw($Bin);
use lib "$Bin";

require "hybrid.pm";
#====================================================================
my (%args) = ();

GetOptions(
	"lm_f=s" => \$args{"lm_f"},
	"lm_e=s" => \$args{"lm_e"},

	"backoff_f|lm_backoff_f=s" => \$args{"lm_backoff_f"},
	"backoff_e|lm_backoff_e=s" => \$args{"lm_backoff_e"},

	"lex=s" => \$args{"lex"},
	"phrase_prob=s" => \$args{"phrase_prob"},

	"debug" => \$args{"debug"}
);
#====================================================================
# MAIN
#====================================================================
main: {
	binmode(STDIN, ":utf8");
	binmode(STDOUT, ":utf8");
	binmode(STDERR, ":utf8");

	if( $args{"debug"} ) {
		foreach my $k ( keys %args ) {
			print STDERR "# args: $k => ".$args{$k}."\n";
		}
	}

	# open DB
	my (%db) = ();
	$db{"lex"} = new Tie::LevelDB::DB($args{"lex"}) if( -e $args{"lex"} );

	$db{"lm_f"} = new Tie::LevelDB::DB($args{"lm_f"}) if( -e $args{"lm_f"} );
	$db{"lm_e"} = new Tie::LevelDB::DB($args{"lm_e"}) if( -e $args{"lm_e"} );

	$db{"lm_backoff_f"} = new Tie::LevelDB::DB($args{"lm_backoff_f"}) if( -e $args{"lm_backoff_f"} );
	$db{"lm_backoff_e"} = new Tie::LevelDB::DB($args{"lm_backoff_e"}) if( -e $args{"lm_backoff_e"} );

	$db{"phrase_prob"} = new Tie::LevelDB::DB($args{"phrase_prob"}) if( -e $args{"phrase_prob"} );

	my $json = JSON->new->allow_nonref;
	while( my $line = <STDIN> ) {
		$line =~ s/\s+$//;

		next if( $line eq "" );

		my ($input, $result, $features) = make_hybrid_feature($json, $line, \%db);	

		print $json->ascii(1)->encode( $features )."\n";
	}
}
#====================================================================
__END__

