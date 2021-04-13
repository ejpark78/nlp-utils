#!/usr/bin/perl
#====================================================================
use strict;
use Encode;
use FileHandle;
use File::Path;
use Getopt::Long;
use Tie::LevelDB; 
#====================================================================
my (%args) = (
	"fields" => "1",
	"weight" => "ngram"
);

GetOptions(
	# "n=i" => \$args{"n"},
	"f|fields=i" => \$args{"fields"},

	# "pos_n1_db=s" => \$args{"pos_n1_db"},
	# "pos_n2_db=s" => \$args{"pos_n2_db"},
	# "pos_n3_db=s" => \$args{"pos_n3_db"},

	# "n1_db=s" => \$args{"n1_db"},
	# "n2_db=s" => \$args{"n2_db"},
	# "n3_db=s" => \$args{"n3_db"},

	# "pos_lm=s" => \$args{"pos_lm"},
	"lm=s" => \$args{"lm"},
	
	"debug" => \$args{"debug"}
);
#====================================================================
# MAIN
#====================================================================
main: {
	ngram_score(\%args);	
}
#====================================================================
# sub functions
#====================================================================
sub ngram_score {
	binmode(STDIN, ":utf8");
	binmode(STDOUT, ":utf8");
	binmode(STDERR, ":utf8");

	my (%param) = (%{shift(@_)});
	$param{"fields"}--;

	if( $param{"debug"} ) {
		foreach my $k ( keys %param ) {
			print STDERR "# param: $k => ".$param{$k}."\n";
		}
	}

	# get sequence
	# print STDERR $param{"n1_db"}."\n" if( -e $param{"n1_db"} );
	# print STDERR $param{"n2_db"}."\n" if( -e $param{"n2_db"} );
	# print STDERR $param{"n3_db"}."\n" if( -e $param{"n3_db"} );

	# print STDERR $param{"pos_n1_db"}."\n" if( -e $param{"pos_n1_db"} );
	# print STDERR $param{"pos_n3_db"}."\n" if( -e $param{"pos_n3_db"} );

	print STDERR $param{"lm"}."\n" if( -e $param{"lm"} );

	# open DB
	my (%ngram_db) = ();

	# $ngram_db{"n1"} = new Tie::LevelDB::DB($param{"n1_db"}) if( -e $param{"n1_db"} );
	# $ngram_db{"n2"} = new Tie::LevelDB::DB($param{"n2_db"}) if( -e $param{"n2_db"} );
	# $ngram_db{"n3"} = new Tie::LevelDB::DB($param{"n3_db"}) if( -e $param{"n3_db"} );

	# $ngram_db{"pos_n1"} = new Tie::LevelDB::DB($param{"pos_n1_db"}) if( -e $param{"pos_n1_db"} );
	# $ngram_db{"pos_n3"} = new Tie::LevelDB::DB($param{"pos_n3_db"}) if( -e $param{"pos_n3_db"} );

	$ngram_db{"lm"} = new Tie::LevelDB::DB($param{"lm"}) if( -e $param{"lm"} );

	my (%ngram) = ();
	while( my $line = <STDIN> ) {
		$line =~ s/\s+$//;

		# print STDERR "# $line:".$db->Get($line)."\n" if( defined($db->Get($line)) );

		next if( $line eq "" );
		# next if( $line =~ /^#/ );

		my (@t) = split(/\t/, $line);
		my (@token) = split(/\s+/, $t[$param{"fields"}]);

		my (%ngram, %count, %common_count) = ();
		# (%{$count{"n1"}}) = get_str_ngram(\@token, 1, \%{$ngram{"n1"}});
		# (%{$common_count{"n1"}}) = get_common_ngram_count(\%ngram_db, \%{$ngram{"n1"}}, 1);

		# (%{$count{"n2"}}) = get_str_ngram(\@token, 2, \%{$ngram{"n2"}});
		# (%{$common_count{"n2"}}) = get_common_ngram_count(\%ngram_db, \%{$ngram{"n2"}}, 2);

		(%{$count{"n3"}}) = get_str_ngram(\@token, 3, \%{$ngram{"n3"}});
		(%{$common_count{"n3"}}) = get_common_ngram_count(\%ngram_db, \%{$ngram{"n3"}}, 3);

		(%{$count{"n4"}}) = get_str_ngram(\@token, 4, \%{$ngram{"n4"}});
		(%{$common_count{"n4"}}) = get_common_ngram_count(\%ngram_db, \%{$ngram{"n4"}}, 4);

		(%{$count{"n5"}}) = get_str_ngram(\@token, 5, \%{$ngram{"n5"}});
		(%{$common_count{"n5"}}) = get_common_ngram_count(\%ngram_db, \%{$ngram{"n5"}}, 5);

		# weight type: 
		#   ngram = count(matched_lm) / count( total_lm )
		#   distribution = 
		#   verb effect = (1+matched_ngram_v) / (1+total_ngram_v)
		#
		#   LM1: ngram
		#   LM2: ngram * distribution 
		#   LM3: ngram * distribution * verb effect
		#
		# http://ko.wikipedia.org/wiki/TF-IDF
		#   ngarm: 불린 빈도: tf(t,d) = 1: t가 d에 한 번이라도 나타나면 1, 아니면 0;
		#   log(tf) => 로그 스케일 빈도: tf(t,d) = log (f(t,d) + 1);
		#   문서 내에서 단어 t의 총 빈도를 f(t,d)라 할 경우, 가장 단순한 tf 산출 방식은 tf(t,d) = f(t,d)로 표현된다. 
		#   augmented(tf) => 증가 빈도: 문서의 길이에 따라 단어의 빈도값 조정 
		#     augmented(tf) = 0.5 + 0.5*f(t,d) / max(f(t,d))
		# y=x/(MAX-MIN)-MIN/(MAX-MIN)

		my (%score) = ();

		foreach my $k ( keys %common_count ) {
			$score{"tf($k)"} = $common_count{$k}{"tf(t,d)"};
			$score{"log($k)"} = $common_count{$k}{"log(t,d)"};
			$score{"bool($k)"} = $common_count{$k}{"bool(t,d)"}/$count{$k}{"total"};
			$score{"idf($k)"} = $common_count{$k}{"idf(t,d,D)"};			
			$score{"augmented($k)"} = $common_count{$k}{"augmented(t,d)"};

			$score{"bool(verb,$k)"} = (1+$common_count{$k}{"bool(verb)"}) / (1+$count{$k}{"v"});
			$score{"bool(distribution,$k)"} = ($common_count{$k}{"bool(distribution)"}/$count{$k}{"token"});
		}

		# $score{"smoothing(log(t,d))"} = ($score{"log(n1)"}+$score{"log(n2)"}*2+$score{"log(n3)"}*3)/6;
		# $score{"smoothing(bool(t,d))"} = ($score{"bool(n1)"}+$score{"bool(n2)"}*2+$score{"bool(n3)"}*3)/6;
		# $score{"smoothing(idf(t,d))"} = ($score{"idf(n1)"}+$score{"idf(n2)"}*2+$score{"idf(n3)"}*3)/6;
		# $score{"smoothing(augmented(t,d))"} = ($score{"augmented(n1)"}+$score{"augmented(n2)"}*2+$score{"augmented(n3)"}*3)/6;

		$score{"LM1"} = $score{"bool(n3)"};
		$score{"LM2"} = $score{"bool(n4)"};
		$score{"LM3"} = $score{"bool(n5)"};
		# $score{"LM2"} = $score{"bool(n3)"} * $score{"bool(distribution,n3)"};
		# $score{"LM3"} = $score{"bool(n3)"} * $score{"bool(distribution,n3)"} * $score{"bool(verb,n3)"};

		# $score{"LM4"} = $score{"log(n3)"};
		# $score{"LM5"} = $score{"augmented(n3)"};

		# $score{"LM6"} = $score{"smoothing(log(t,d))"};
		# $score{"LM7"} = $score{"smoothing(bool(t,d))"};
		# $score{"LM8"} = $score{"smoothing(idf(t,d))"};
		# $score{"LM9"} = $score{"smoothing(augmented(t,d))"};

		printf "%f\t%f\t%f\t%s\n", 
			$score{"bool(n3)"}, $score{"bool(n4)"}, $score{"bool(n5)"},
			$line;

		# printf "%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%s\n", 
		# 	$score{"LM1"}, $score{"LM2"}, $score{"LM3"},
		# 	$score{"LM4"}, $score{"LM5"}, $score{"LM6"},
		# 	$score{"LM7"}, $score{"LM8"}, $score{"LM9"},
		# 	$line;

		if( $param{"debug"} ) {
			print STDERR "\n";
			print STDERR "# ngram_score \n";
			# print STDERR "# count: ".get_hash_str(\%count)."\n" if( $param{"debug"} );
			# print STDERR "# * common_count: \n# - ".get_hash_str_2key(\%common_count)."\n";
			print STDERR "# * score: \n# - ".get_hash_str(\%score)."\n";

			printf STDERR "%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%s\n", 
				$score{"LM1"}, $score{"LM2"}, $score{"LM3"},
				$score{"LM4"}, $score{"LM5"}, $score{"LM6"},
				$score{"LM7"}, $score{"LM8"}, $score{"LM9"},
				$line;

			print STDERR "#===================================== \n";
		}
	}
}
#====================================================================
sub get_hash_str
{
	my (%data) = %{shift(@_)};

	my (@buf) = ();
	foreach my $k ( sort keys %data ) {
		push(@buf, "$k=>".sprintf("%.2f", $data{$k}));
	}

	return join(", \n# - ", @buf);
}
#====================================================================
sub get_hash_str_2key
{
	my (%data) = %{shift(@_)};

	my (@buf) = ();
	foreach my $k ( sort keys %data ) {
		foreach my $kk ( sort keys %{$data{$k}} ) {
			push(@buf, "$k=>$kk=>".sprintf("%.2f", $data{$k}{$kk}));
		}
	}

	return join(", \n# - ", @buf);
}
#====================================================================
sub get_common_ngram_count
{
	my (%ngram_db) = %{shift(@_)};
	my (%ngram) = %{shift(@_)};
	my $n = shift(@_);

	my (%uniq, @common, @common_dist, @common_pos) = ();
	my (%common_count) = (

		"max(tf)" => 0, 

		"tf(t,d)" => 0, 
		"tf(pos)" => 0, 
		"tf(verb)" => 0, 
		"tf(distribution)" => 0, 

		"idf(t,d,D)" => 0,

		"log(t,d)" => 0, 
		"augmented(t,d)" => 0, 		

		"bool(t,d)" => 0, 
		"bool(pos)" => 0, 
		"bool(verb)" => 0, 
		"bool(distribution)" => 0
	);

	my (@tf_list) = ();

	my $df = 20796986;

	foreach my $np_pos ( keys %ngram ) {
		# with pos tag
		if( defined($ngram_db{"pos_n$n"}) && defined($ngram_db{"pos_n$n"}->Get($np_pos)) ) {
			push(@common_pos, $np_pos." (".$ngram_db{"pos_n$n"}->Get($np_pos).")");
			$common_count{"tf(pos)"} += $ngram_db{"pos_n$n"}->Get($np_pos);
			$common_count{"bool(pos)"}++;

			$common_count{"bool(verb)"}++ if( $np_pos =~ /\/V/i );
		}

		# without pos tag
		my $np = $np_pos;
		$np =~ s/\/[A-Z]+?/ /g;

		if( defined($ngram_db{"lm"}) && defined($ngram_db{"lm"}->Get($np)) ) {
			my $tf = $ngram_db{"lm"}->Get($np);

			push(@common, $np." ($tf)");
			push(@tf_list, $tf);

			$common_count{"bool(t,d)"}++;
			# $common_count{"tf(t,d)"} += $tf;
			# $common_count{"log(t,d)"} += log($tf);
			# $common_count{"idf(t,d,D)"} += log($df/$tf);

			$common_count{"max(tf)"} = $tf if( $common_count{"max(tf)"} < $tf );

			# count distribution
			foreach my $w ( split(/\s+/, $np) ) {
				if( !defined($uniq{$w}) && defined($ngram_db{"lm"}->Get($w)) ) {
					push(@common_dist, $w."(".$ngram_db{"lm"}->Get($w).")");
					$common_count{"tf(distribution)"} += $ngram_db{"lm"}->Get($w);
					$common_count{"bool(distribution)"}++;
				}
				$uniq{$w} = 1;
			}
		}
	}

	my $avg = ($common_count{"tf(t,d)"}+1)/(scalar(@tf_list)+1);

	foreach my $tf ( @tf_list ) {
		# $common_count{"augmented(t,d)"} += ( 0.5 + (0.5 * $tf + 1) / ($common_count{"max(tf)"} + 1) );
		if( $tf > $avg) {
			$common_count{"augmented(t,d)"} += 0.5;
		} else {
			$common_count{"augmented(t,d)"} += 1;
		}		
	}

	$common_count{"log(t,d)"} = ($common_count{"log(t,d)"}+1) / (scalar(@tf_list)+1);
	$common_count{"idf(t,d,D)"} = ($common_count{"idf(t,d,D)"}+1) / (scalar(@tf_list)+1);
	$common_count{"augmented(t,d)"} = ($common_count{"augmented(t,d)"}+1) / (scalar(@tf_list)+1);

	if( $args{"debug"} ) {
		print STDERR "\n";
		print STDERR "## get_common_ngram_count: $n \n";
		print STDERR "# unigram index: (".scalar(keys %uniq).") ".join(" ||| ", keys %uniq)."\n";
		print STDERR "# common ngram: (".scalar(@common).") ".join(" ||| ", @common)."\n";
		print STDERR "# common pos ngram: (".scalar(@common_pos).") ".join(" ||| ", @common_pos)."\n";
		print STDERR "# common dist ngram: (".scalar(@common_dist).") ".join(" ||| ", @common_dist)."\n";
	}

	return (%common_count);
}
#====================================================================
sub get_str_ngram
{
	my (@token) = (@{shift(@_)});
	my $n = shift(@_);
	my $ret = shift(@_);

	$n--;

	for( my $i=0 ; $i<scalar($n) ; $i++ ) {
		unshift(@token, "<s>");
		push(@token, "</s>");
	}

	my (%count) = ("total" => 0, "v" => 0, "token_v" => 0);
	foreach my $w ( @token ) {
		$count{"token_v"} ++ if( $w =~ /\/V/i );
	}

	for( my $i=0 ; $i<scalar(@token)-$n ; $i++ ) {
		my $buf = join(" ", @token[$i..$i+$n]);

		$buf =~ s/\s+$//;

		next if( $buf eq "" );

		$ret->{$buf} = 1;

		$count{"total"}++;
		$count{"v"}++ if( $buf =~ /\/V/i );
	}

	if( $args{"debug"} ) {
		print STDERR "\n";
		print STDERR "### get_str_ngram: n=$n\n";
		print STDERR "# input token (n: $n): ".join(" ", @token)."\n";
		print STDERR "# ngram list: (".scalar(keys %{$ret}).") ".join(" ||| ", keys %{$ret})."\n";
	}

	$count{"token"} = scalar(@token);
	$count{"total"} = -1 if( $count{"total"} == 0 );

	return (%count);
}
#====================================================================
__END__

