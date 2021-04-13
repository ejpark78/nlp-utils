#!/usr/bin/perl
#====================================================================
use strict;
use Encode;
use FileHandle;
use File::Path;
use Getopt::Long;
use Data::Printer;
use JSON;
use BerkeleyDB;

use FindBin qw($Bin);
use lib "$Bin";

require "hybrid.pm";
#====================================================================
our (%args) = (
	"class" => "tm-2M:-1,drama-2.9M:0,movies-3.2M:1",
	"home" => "/home/ejpark/workspace/model/ko-en"
);

GetOptions(
	"columns=s" => \$args{"columns"},
	"class=s" => \$args{"class"},
	"home=s" => \$args{"home"},
	"debug" => \$args{"debug"},
	"json" => \$args{"json"},
	"svm" => \$args{"svm"},
);
#====================================================================
# MAIN
#====================================================================
main: {
	binmode(STDIN, ":utf8");
	binmode(STDOUT, ":utf8");
	binmode(STDERR, ":utf8");

	# printf STDERR "home: %s\n", $args{"home"};
	# printf STDERR "class: %s\n", $args{"class"};

	# open DB
	my (%model) = (parse_hybrid_class($args{"class"}));

	my (%db_name) = (
		"lex" => "lex_prob.db",
		"phrase_table" => "phrase-table.db",

		"e_lm" => "en_lm.db",
		"f_lm" => "ko_lm.db",

		"e_backoff" => "en_backoff.db",
		"f_backoff" => "ko_backoff.db",
	);

	my $home = $args{"home"};

	my (%db) = ();
	foreach my $m ( keys %model ) {
		foreach my $k ( keys %db_name ) {
			my $fn = sprintf("%s/%s/%s", $home, $m, $db_name{$k});

			if( !-e $fn ) {
				die("ERROR: File not exists: ".$fn."\n");
			}

			$db{$m}{$k} = new BerkeleyDB::Btree(-Filename=>$fn, -Flags=>DB_CREATE)
							or die("ERROR: Cannot open ".$fn.": ".$!." ".$BerkeleyDB::Error."\n");
		}
	}

	# extract features
	my (@title) = ();

	my $cnt = 0;
	my $json = JSON->new->allow_nonref;
	while( my $line = <STDIN> ) {
		$line =~ s/\s+$//;

		next if( $line eq "" );

		my ($input, $features) = make_hybrid_feature($json, $line, \%db);	

		if( scalar(@title) == 0 ) {
			foreach my $m ( sort keys %{$features} ) {
				foreach my $t ( sort keys %{$features->{$m}} ) {
					next if( $m =~ m/:1$/ );

					push(@title, "$m $t");
				}
			}

			printf "bleu\tclass\t%s\n", join("\t", @title);
		}

		if( $args{"debug"} ) {
			print STDERR Dumper($features);
		}

		if( $args{"json"} ) {
			print $json->ascii(1)->encode( $features )."\n";
		} else {
			my $class = get_class(\%model, $input, $features);

			my $i = 1;
			my (@result) = ();

			foreach my $m ( sort keys %{$features} ) {
				foreach my $t ( sort keys %{$features->{$m}} ) {
					next if( $m =~ m/:1$/ );
					
					push(@result, sprintf("%d:%s", $i++, $features->{$m}{$t}));
				}
			}

			# printf STDERR "%0.4f\n", $input->{$class}{"bleu"};
			printf "%0.4f\t%s\t%s\n", $input->{$class}{"bleu"}, $model{$class}, join("\t", @result);
		}

		printf STDERR "\r(%07d)", $cnt if( $cnt++ % 10 == 0 );
	}

	printf STDERR "(%07d)\n", $cnt++;
}
#====================================================================
__END__

