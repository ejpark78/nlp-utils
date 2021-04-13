#!/usr/bin/perl
#====================================================================
use strict;
use Encode;
use FileHandle;
use File::Path;
use Getopt::Long;
use POSIX;
use JSON;

use FindBin qw($Bin);
use lib "$Bin";

require "hybrid.pm";
#====================================================================
our (%args) = (
		"class" => "tm-2M:-1,drama-2.9M:0,movies-3.2M:1",
		"prefix" => ""
);

GetOptions(
	"class=s" => \$args{"class"},
	"prefix=s" => \$args{"prefix"},
	"debug" => \$args{"debug"},
);
#====================================================================
# MAIN
#====================================================================
main: {
	binmode(STDIN, ":utf8");
	binmode(STDOUT, ":utf8");
	binmode(STDERR, ":utf8");

	# open DB
	my (%model) = (get_class_name($args{"class"}));

	my (@model_names) = (values %model);

	my (@src, @ref, %tst, %p_count) = ();

	my $json = JSON->new->allow_nonref;
	while( my $line = <STDIN> ) {
		$line =~ s/\s+$//;

		next if( $line eq "" );

		my ($predict, $str_json) = split(/\t/, $line, 2);
		$p_count{$predict}++;

		my $decoded = $json->decode( $str_json );

		my $m = $model{$predict};

		push(@src, $decoded->{"source"});

		my (@buf_ref) = ();
		if( defined($decoded->{"ref"}) ) {
			push(@buf_ref, $decoded->{"ref"});
		} else {
			for( my $i=0 ; $i<5 ; $i++ ) {
				next if( !defined($decoded->{"ref$i"}) );

				push(@buf_ref, $decoded->{"ref$i"});
			}
		}
		push(@ref, join("\t", @buf_ref));

		push(@{$tst{"best"}}, get_best_bleu(\@model_names, $decoded));		
		push(@{$tst{"svm_best"}}, $decoded->{"$m:model"});		

		foreach my $k ( @model_names ) {
			push(@{$tst{$k}}, $decoded->{"$k:model"});		
		}
	}

	# save
	my $p = $args{"prefix"};
	$p .= "." if( $p ne "" );

	save_as_file("src", $p."src", \@src);
	save_as_file("ref", $p."ref", \@ref);

	save_as_file("tst", $p."tst.best", \@{$tst{"best"}});
	auto_eval($p."src", $p."ref", $p."tst.best");

	save_as_file("tst", $p."tst.svm_best", \@{$tst{"svm_best"}});
	auto_eval($p."src", $p."ref", $p."tst.svm_best");

	foreach my $k ( @model_names ) {
		save_as_file("tst", $p."tst.$k", \@{$tst{$k}});
		auto_eval($p."src", $p."ref", $p."tst.$k");
	}

	# auto eval
	my $cmd = "sync; grep_bleu.sh";
	safesystem($cmd);	

	foreach my $predict ( sort keys %p_count ) {
		printf "%d\t%d\n", $predict, $p_count{$predict};
	}

	# clean
	$cmd = "rm ".$p."src ".$p."src.sgm ".$p."ref ".$p."src.sgm";
	safesystem($cmd);	

	foreach my $k ( @model_names ) {
		$cmd = "rm ".$p."tst.$k ".$p."tst.$k.sgm";
		safesystem($cmd);	
	}
}
#====================================================================
sub get_best_bleu {
	my (@model_names) = (@{shift(@_)});
	my $decoded = shift(@_);

	my $tst = "";
	my $bleu = 0;
	foreach my $m ( @model_names ) {
		my $b = $decoded->{"$m:bleu"};

		if( $bleu < $b ) {
			$bleu = $b;
			$tst = $decoded->{"$m:model"};
		}
	}

	return $tst;
}
#====================================================================
sub auto_eval {
	my $src = shift(@_);
	my $ref = shift(@_);
	my $tst = shift(@_);

	my $cmd = "mteval-v13a.pl -s $src.sgm -r $ref.sgm -t $tst.sgm > $tst.bleu; sync";
	safesystem($cmd);
}
#====================================================================
sub save_as_file {
	my $type = shift(@_);
	my $fn = shift(@_);
	my (@data) = (@{shift(@_)});

	open(FILE, ">", $fn);
	binmode(FILE, ":utf8");

	foreach my $line ( @data ) {
		print FILE $line."\n";
	}

	close(FILE);

	my $cmd = "sync; wrap.pl -type $type -in $fn -out $fn.sgm; sync";
	safesystem($cmd);
}
#====================================================================
sub safesystem {
	print STDERR "Executing: @_\n\n";

	system(@_);

	if( $? == -1 ) {
		print STDERR "Failed to execute: @_\n  $!\n";
		exit(1);
	} elsif( $? & 127 ) {
		printf STDERR "Execution of: @_\n  died with signal %d, %s coredump\n", ($? & 127),  ($? & 128) ? 'with' : 'without';
		exit(1);
	} else {
		my $exitcode = $? >> 8;
		print STDERR "Exit code: $exitcode\n" if $exitcode;
		return ! $exitcode;
	}
	
	print STDERR "\n";
}
#====================================================================
__END__

