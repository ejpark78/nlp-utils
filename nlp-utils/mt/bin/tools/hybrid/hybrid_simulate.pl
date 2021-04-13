#!/usr/bin/perl

use strict;
use Encode;
use Getopt::Long;


our (%args) = ();

GetOptions(
	"prefix=s" => \$args{"prefix"},
	"predict=s" => \$args{"predict"},
	"up_out=s" => \$args{"up_out"},
	"debug" => \$args{"debug"},
	"sentence-bleu" => \$args{"sentence-bleu"},
);


main:{
	binmode(STDIN, ":utf8");
	binmode(STDOUT, ":utf8");
	binmode(STDERR, ":utf8");

	my $tst_set = "";
	my (%data) = ();
	foreach my $fn ( @ARGV ) {
		$fn = decode("utf8", $fn);

		if( $tst_set eq "" ) {
			$tst_set = $fn;
			$tst_set =~ s/\.tok\..+$//;
		}

		my $domain = $fn;
		$domain =~ s/^.+-//;
		$domain =~ s/^.+\.tok\.//;
		$domain =~ s/\.bleu.*$//;
		$domain =~ s/\.sent_bleu.*$//;
		$domain =~ s/\.bleu_score$//;
		$domain =~ s/\.bleu_merged$//;

		print STDERR "fn:", $fn, "\t", "domain:", $domain, "\n";		
		push(@{$data{$domain}}, read_bleu($fn, $args{"sentence-bleu"}));
	}

	# autoeval upperbound
	my (@upperbound) = ();
	foreach my $domain ( sort keys %data ) {
		my (@data_domain) = (@{$data{$domain}});
		print STDERR $domain, ": ", scalar(@data_domain), "\n";

		get_upperbound($domain, $data{$domain}, \@upperbound);
	}

	my (%up_count) = ();
	for( my $i=0 ; $i<scalar(@upperbound) ; $i++ ) {
		$up_count{$upperbound[$i]->{"domain"}}++;
	}

	if( !defined($args{"up_out"}) ) {
		$args{"up_out"} = $args{"prefix"}.".up_out";
	}

	if( $args{"up_out"} ) {
		printf STDERR "up_out: %s\n", $args{"up_out"};
		
		die "can not open : ".$args{"up_out"}." $!\n" unless( open(FILE, ">", $args{"up_out"}) );
		binmode(FILE, "utf8");

		my (@cols) = qw/ domain bleu tst src refs /;
		# printf FILE "%s\n", join("\t", @cols);
		for( my $i=0 ; $i<scalar(@upperbound) ; $i++ ) {
			my (@refs) = split(/\t/, $upperbound[$i]->{"ref"});
			
			(@cols) = ();
			push(@cols, $upperbound[$i]->{"domain"});
			push(@cols, $upperbound[$i]->{"bleu"});
			push(@cols, $upperbound[$i]->{"tst"});
			push(@cols, $upperbound[$i]->{"src"});

			printf FILE "%s\t%s\n", join("\t", @cols), join("\t", @refs); 
		}

		close(FILE);
	}

	# autoeval up
	printf STDERR "run auto eval up: %d\n", scalar(@upperbound);
	run_mteval($args{"prefix"}, "up", \@upperbound);

	# autoeval predict
	if( -f $args{"predict"} ) {
		my (@predict) = ();
		my (%by_class) = ();
		my (%by_class_alias2all) = ();

		my $cnt = 0;
		my $diff_bleu = 0;

		my (@predict_class) = read_predict($args{"predict"});
		for( my $i=0 ; $i<scalar(@predict_class) ; $i++ ) {
			my $class = $predict_class[$i];

			# printf STDERR "%d\t%s\t%s\n", $i, $upperbound[$i]->{"domain"}, $class;
			
			if( $upperbound[$i]->{"domain"} ne $class ) { # && $upperbound[$i]->{"bleu"} > $data{$class}[$i]->{"bleu"}
				printf "%d\t%s\n", $i, $upperbound[$i]->{"src"};
				printf "ref: %s\n", $upperbound[$i]->{"ref"};
				printf "up: %s\t%s\t%s\n", $upperbound[$i]->{"domain"}, $upperbound[$i]->{"bleu"}, $upperbound[$i]->{"tst"};
				printf "predict: %s\t%s\t%s\n", $class, $data{$class}[$i]->{"bleu"}, $data{$class}[$i]->{"tst"};
				printf "\n";

				$diff_bleu += ($upperbound[$i]->{"bleu"} - $data{$class}[$i]->{"bleu"});
			} else {
				$cnt++;
			}

			push(@predict, $data{$class}[$i]);
			push(@{$by_class{$class}}, $data{$class}[$i]);
			push(@{$by_class_alias2all{$class}}, $data{"all"}[$i]);
		}

		my $total = scalar(@predict_class);
		printf "%.2f = %d / %d, %.4f\n", $cnt / $total, $cnt, $total, $diff_bleu;

		if( scalar(@predict_class) > 0 ) {
			print "run auto eval predict:", scalar(@predict), "\n";		
			run_mteval($args{"prefix"}, "predict", \@predict);

			# # get bleu class only
			# foreach my $class ( keys %by_class ) {
			# 	printf "%s\t%d\n", $class, scalar(@{$by_class{$class}});
				
			# 	run_mteval($args{"prefix"}, "predict.$class", \@{$by_class{$class}});
			# } 

			# # get alias bleu 
			# foreach my $class ( keys %by_class_alias2all ) {
			# 	printf "%s\t%d\n", $class, scalar(@{$by_class_alias2all{$class}});
				
			# 	run_mteval($args{"prefix"}, "alias2all.$class", \@{$by_class_alias2all{$class}});
			# } 
		}
	}
}


sub run_mteval {
	my $prefix = shift(@_);
	my $tag = shift(@_);
	my (@rows) = (@{shift(@_)});

	printf STDERR "prefix: %s\n", $prefix;

	my (@src, @ref, @best) = ();
	for( my $i=0 ; $i<scalar(@rows) ; $i++ ) {
		push(@src, $rows[$i]{"src"});
		push(@ref, $rows[$i]{"ref"});
		push(@best, $rows[$i]{"tst"});
	}

	my ($f_src, $f_ref, $f_tst) = ("$prefix.$tag.src", "$prefix.$tag.ref", "$prefix.$tag");

	save_as_file("src", $f_src, \@src);
	save_as_file("ref", $f_ref, \@ref);
	save_as_file("tst", $f_tst, \@best);

	my $cmd = "sync && mteval-v13a.pl ";
	$cmd .= "-s \"$f_src.sgm\" ";
	$cmd .= "-r \"$f_ref.sgm\" ";
	$cmd .= "-t \"$f_tst.sgm\" ";
	$cmd .= "> \"$f_tst.bleu\"";

	safesystem($cmd);

	$cmd = "sync && rm \"$f_src\" \"$f_ref\" \"$f_src.sgm\" \"$f_ref.sgm\" \"$f_tst.sgm\"";
	safesystem($cmd);
}


sub read_predict {
	my $fn = shift(@_);

	my ($open_mode, $file_type) = ("<", `file $fn`);

	$open_mode = "<:gzip" if( $file_type =~ m/ gzip compressed data,/ );
	die "can not open : $fn $!\n" unless( open(FILE, $open_mode, $fn) );

	binmode(FILE, "utf8");

	my (%index) = ();

	my (@ret) = ();
	foreach my $domain ( <FILE> ) {
		($domain) = split(/\t/, $domain);
		$domain =~ s/^\s+|\s+$//g;

		next if( $domain eq "predict" || $domain eq "domain" );
		$domain = "all" if( $domain eq "a");

		$domain =~ s/\.0$//;
		push(@ret, $domain);

		$index{$domain}++;
	}

	printf STDERR "read_predict count:\n";
	foreach my $domain ( sort keys %index ) {
		printf STDERR "%s\t%d\n", $domain, $index{$domain};
	}

	close(FILE);

	return (@ret);
}


sub read_bleu {
	my $fn = shift(@_);
	my $sentence_bleu = shift(@_);

	my ($open_mode, $file_type) = ("<", `file $fn`);

	$open_mode = "<:gzip" if( $file_type =~ m/ gzip compressed data,/ );
	die "can not open : $fn $!\n" unless( open(FILE, $open_mode, $fn) );

	binmode(FILE, "utf8");

	my (@ret) = ();
	foreach my $line ( <FILE> ) {
		$line =~ s/^\s+|\s+$//g;

		my ($s_id, $bleu, $nist, $src, $tst, $ref) = ();
		if( $sentence_bleu ) {
			($bleu, $tst, $src, $ref) = split(/\t/, $line, 4);
			$nist = -1;
		} else {
			next if( $line !~ /# Sentence BLEU:/ );

			$line =~ s/# Sentence BLEU:\s+//;

			($s_id, $bleu, $nist, $src, $tst, $ref) = split(/\t/, $line, 6);
		}

		my (%row) = (
			"bleu" => $bleu,  
			"nist" => $nist,  
			"src" => $src,  
			"tst" => $tst,  
			"ref" => $ref
		);

		push(@ret, \%row);
	}

	close(FILE);

	return (@ret);
}


sub copy_value {
	my $domain = shift(@_);
	my $a = shift(@_);
	my $b = shift(@_);

	my (@keys) = qw/ src tst ref bleu nist /;
	foreach my $k ( @keys ) {
		$a->{$k} = $b->{$k};
	}

	$a->{"domain"} = $domain;
}


sub get_upperbound {
	my $domain = shift(@_);
	my (@data_domain) = (@{shift(@_)});
	my $upperbound = shift(@_);

	for( my $i=0 ; $i<scalar(@data_domain) ; $i++ ) {
		if( !defined($upperbound->[$i]) ) {
			copy_value($domain, $upperbound->[$i], $data_domain[$i]);
		}

		if( $upperbound->[$i]{"bleu"} < $data_domain[$i]->{"bleu"} ) {
			copy_value($domain, $upperbound->[$i], $data_domain[$i]);
		} elsif( $upperbound->[$i]{"bleu"} == $data_domain[$i]->{"bleu"} && 
				$upperbound->[$i]{"nist"} < $data_domain[$i]->{"nist"} ) {
			copy_value($domain, $upperbound->[$i], $data_domain[$i]);
		} 
	}
}


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

	my $cmd = "sync && wrap.pl -type $type -in \"$fn\" -out \"$fn.sgm\"";
	safesystem($cmd);
}


sub safesystem {
	# print STDERR "Executing: @_\n";

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


__END__

