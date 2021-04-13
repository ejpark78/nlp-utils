#!/usr/bin/perl
#====================================================================
use strict;
use Encode;
use FileHandle;
use File::Path;
use Getopt::Long;
use POSIX;
use BerkeleyDB; 
#====================================================================
our (%args) = (
	"n" => "3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25",

	"max_iter" => 10,
	"max_ncluster" => 5,
	
	"th_idf" => 5.0,
	"th_ngram" => -1,	
	"th_ngram_freq" => 5,
	"th_min_sentence" => 1,
	"th_similarity" => 0.2,
	"th_cluster_size" => 10,

	"prefix" => "bitext.",
	"prefix_cluster" => "bitext.",

	"ngram_count" => "data.n-40.ngram_count.berkeleydb",
);

GetOptions(
	"n=s" => \$args{"n"},
	"ngram_count=s" => \$args{"ngram_count"},

	"prefix=s" => \$args{"prefix"},
	"prefix_cluster=s" => \$args{"prefix_cluster"},

	"max_iter=i" => \$args{"max_iter"},
	"max_ncluster=i" => \$args{"max_ncluster"},

	"th_idf=f" => \$args{"th_idf"},
	"th_ngram=i" => \$args{"th_ngram"},
	"th_similarity=f" => \$args{"th_similarity"},
	"th_ngram_freq=i" => \$args{"th_ngram_freq"},
	"th_min_sentence=i" => \$args{"th_min_sentence"},

	"th_cluster_size=i" => \$args{"th_cluster_size"},

	"clean" => \$args{"clean"},
	"build_index" => \$args{"build_index"},

	"clean_cluster" => \$args{"clean_cluster"},	
	"build_cluster" => \$args{"build_cluster"},

	"merge_cluster" => \$args{"merge_cluster"},	
	"merge_cluster_by_size" => \$args{"merge_cluster_by_size"},	
	"remove_cluster_by_size" => \$args{"remove_cluster_by_size"},	

	"report" => \$args{"report"},	
	"show_cluster" => \$args{"show_cluster"},
	"save_cluster_status" => \$args{"save_cluster_status"},

	"with_bitext" => \$args{"with_bitext"},	
	"without_feature_extend" => \$args{"without_feature_extend"},	
);
#====================================================================
# MAIN
#====================================================================
our $start_time = time;

our $total_sentence = -1;

our (%dictionary_bitext) = ();
our (%dictionary_ngram_count) = ();

our (%dictionary_feature_map) = ();
our (%dictionary_feature_index) = ();
our (%dictionary_feature_ngram) = ();

our (%dictionary_cluster) = ();
our (%dictionary_cluster_feature) = ();
our (%dictionary_cluster_history) = ();

our (%dictionary_name) = (
	"bitext" => "sentence.berkeleydb", # id = sentence

	"feature_map" => "feature_map.berkeleydb", # sentence id = feature list
	"feature_index" => "feature_index.berkeleydb", # feature = sentence id list
	"feature_ngram" => "feature_ngram.berkeleydb", # ngram size = feature list

	"cluster" => "cluster.berkeleydb", # cluster id = sentence id list
	"cluster_feature" => "cluster_feature.berkeleydb", # cluster id = feature list
	"cluster_history" => "cluster_history.berkeleydb", # ngram size = cluster id\tsentence list
);

our (%stop_word) = (
	"." => 1,
	"," => 1,
	"%" => 1,
	"!" => 1,
	"..." => 1,
	"?" => 1,
	":" => 1,
	";" => 1,
);

main: {
	#================================================================
	binmode(STDIN, ":utf8");
	binmode(STDOUT, ":utf8");
	binmode(STDERR, ":utf8");
	#================================================================
	my (@n_list) = sort {$b<=>$a} split(/,/, $args{"n"});

	$args{"th_ngram"} = ( $args{"th_ngram"} < 0 ) ? $n_list[0] : $args{"th_ngram"};

	update_dictionary_name();

	if( $args{"clean"} ) {
		clean_dictionary();
		exit(1);	
	}

	if( $args{"clean_cluster"} ) {
		reset_cluster_dictionary();
		exit(1);
	}

	open_dictionary();

	if( $args{"build_index"} ) {
		convert_bitext_to_db(\@n_list, $args{"th_ngram_freq"});

		close_dictionary();
		exit(1);	
	}

	$total_sentence = $dictionary_bitext{"_TOTAL_"};

	open_cluster_dictionary();

	if( $args{"build_cluster"} ) {
		build_cluster();
	}

	if( $args{"merge_cluster"} ) {
		merge_cluster_by_similarity();
	}

	if( $args{"merge_cluster_by_size"} ) {
		merge_cluster_by_size();
	}

	if( $args{"remove_cluster_by_size"} ) {
		remove_cluster_by_size();
	}

	if( $args{"report"} ) {
		report_cluster();
	}

	if( $args{"show_cluster"} ) {
		show_cluster();
	}

	# unload dictionary
	close_dictionary();

	print_runtime("main");
}
#====================================================================
# sub functions																						
#====================================================================
sub show_cluster_status {
}
#====================================================================
sub save_cluster_status {
	return if( $args{"save_cluster_status"} );

	# clear history
	foreach my $n ( keys %dictionary_cluster_history ) {
		next if( $n ne $args{"th_ngram"} );

		delete $dictionary_cluster_history{$n};
	}

	foreach my $c_id ( sort {$a<=>$b} keys %dictionary_cluster ) {
		next if( substr($c_id, 0, 1) eq "_" );

		my (@sub_cluster) = to_list($dictionary_cluster{$c_id});

		$dictionary_cluster_history{$args{"th_ngram"}} = sprintf("%d\t%s", $c_id, join("\t", @sub_cluster));
	}
}
#====================================================================
sub show_cluster {
	my $n_cluster = scalar keys %dictionary_cluster;
	printf "# n cluster: %d, %d\n", $n_cluster, $dictionary_cluster{"_TOTAL_"};

	foreach my $c_id ( sort {$a<=>$b} keys %dictionary_cluster ) {
		next if( substr($c_id, 0, 1) eq "_" );

		my (%sub_cluster) = to_hash($dictionary_cluster{$c_id});

		printf "# cluster id: %d, count: %s\n", $c_id, comma(scalar keys %sub_cluster);
		# printf "# feature list: %s\n", $dictionary_cluster_feature{$c_id};

		foreach my $s_id ( keys %sub_cluster ) {
			next if( !defined($dictionary_bitext{$s_id}) );

			my ($a, $s) = split(/\t/, $dictionary_bitext{$s_id});
			printf "%d\t%s\n", $c_id, $s;
		}
	}
}
#====================================================================
sub show_sub_cluster {
	my $c_id = shift(@_);

	return if( substr($c_id, 0, 1) eq "_" );

	my (%sub_cluster) = to_hash($dictionary_cluster{$c_id});

	printf "# cluster id: %d, count: %d\n", $c_id, scalar keys %sub_cluster;
	foreach my $s_id ( keys %sub_cluster ) {
		next if( !defined($dictionary_bitext{$s_id}) );

		printf "%d\t%s\n", $c_id, $dictionary_bitext{$s_id};
	}
}
#====================================================================
sub get_cluster_size {
	my (@cluster) = (@_);

	my (%cluster_size) = ();
	foreach my $c_id ( @cluster ) {
		next if( substr($c_id, 0, 1) eq "_" );

		my (@sub_cluster) = to_list($dictionary_cluster{$c_id});

		my $size = scalar @sub_cluster;
		$cluster_size{$size}{$c_id} = 1;
	}

	my (@s_list) = ();
	foreach my $size ( sort {$a<=>$b} keys %cluster_size ) {
		my (@list) = sort {$a<=>$b} keys %{$cluster_size{$size}};

		# printf "# %d \n", $size;
		# printf "# %d : %s\n", $size, join("|", @list);
		push(@s_list, @list);
	}

	return (@s_list);
}
#====================================================================
sub merge_cluster_by_size {
	my (@cluster) = keys %dictionary_cluster;
	my (@s_list)  = get_cluster_size(@cluster);

	my (@big_cluster) = ();

	my $i = 0;
	foreach my $s_id ( @s_list ) {
		my (@sub_cluster) = to_list($dictionary_cluster{$s_id});

		$i++ if( $args{"th_cluster_size"} < scalar @sub_cluster && defined($big_cluster[$i]) ); 

		push(@{$big_cluster[$i]}, @sub_cluster);

		my $cluster_size = scalar @{$big_cluster[$i]};
		$i++ if( $args{"th_cluster_size"} < $cluster_size ); 
	}

	my $total = 0;
	my (%uniq_sentence) = ();
	for(my $i=0 ; $i<scalar(@big_cluster) ; $i++ ) {
		foreach my $s_id ( @{$big_cluster[$i]} ) {
			$uniq_sentence{$s_id} = 1;
		}

		my $cluster_size = scalar @{$big_cluster[$i]};
		$total += $cluster_size;

		my $msg = sprintf("# cluster_info: %3d\t%s", $i, comma($cluster_size));

		printf "%s\n", $msg;
		printf STDERR "%s\n", $msg;

		if( $args{"with_bitext"} ) {
			foreach( my $j=0 ; $j<scalar(@{$big_cluster[$i]}) ; $j++  ) {
				my $s_id = $big_cluster[$i][$j];

				printf "# bitext:\t%d\t%s\n", $i, decode("utf8", $dictionary_bitext{$s_id});
			}
			printf "\n";
		}
	}

	if( $args{"with_bitext"} ) {
		foreach my $s_id ( keys %dictionary_bitext ) {
			next if( substr($s_id, 0, 1) eq "_" );
			next if( defined($uniq_sentence{$s_id}) );

			printf "# bitext:\t%d\t%s\n", -1, decode("utf8", $dictionary_bitext{$s_id});
		}
	}

	my $n_uniq = scalar keys %uniq_sentence;
	my $msg = sprintf("# cluster_info: th_ngram: %3d, unique sentence: %s, total: %s, overlap: %s", 
					$dictionary_cluster{"_TH_NAGRM_"}, 
					comma($n_uniq), 
					comma($total),
					comma($total - $n_uniq));

	printf "%s\n", $msg;
	printf STDERR "%s\n", $msg;

	print_runtime((caller(0))[3]);
}
#====================================================================
sub update_dictionary_name {
	return if( $args{"prefix"} eq "" );

	foreach my $db_name ( keys %dictionary_name ) {
		if( $db_name =~ /cluster/ ) {
			$dictionary_name{$db_name} = sprintf("%s%s", $args{"prefix_cluster"}, $dictionary_name{$db_name});
		} else {
			$dictionary_name{$db_name} = sprintf("%s%s", $args{"prefix"}, $dictionary_name{$db_name});
		}
	}

	# foreach my $db_name ( keys %dictionary_name ) {
	# 	printf "# %s\t%s\n", $db_name, $dictionary_name{$db_name};
	# }
}
#====================================================================
sub open_cluster_dictionary {
	tie(%dictionary_cluster, 		 "BerkeleyDB::Btree", -Flags=>DB_CREATE, -Filename=>$dictionary_name{"cluster"});
	tie(%dictionary_cluster_feature, "BerkeleyDB::Btree", -Flags=>DB_CREATE, -Filename=>$dictionary_name{"cluster_feature"});
	tie(%dictionary_cluster_history, "BerkeleyDB::Btree", -Flags=>DB_CREATE, -Filename=>$dictionary_name{"cluster_history"});
}
#====================================================================
sub open_dictionary {
	tie(%dictionary_ngram_count,   "BerkeleyDB::Btree", -Flags=>DB_CREATE, -Filename=>$args{"ngram_count"});

	tie(%dictionary_bitext, 	   "BerkeleyDB::Btree", -Flags=>DB_CREATE, -Filename=>$dictionary_name{"bitext"});

	tie(%dictionary_feature_map,   "BerkeleyDB::Btree", -Flags=>DB_CREATE, -Filename=>$dictionary_name{"feature_map"});
	tie(%dictionary_feature_index, "BerkeleyDB::Btree", -Flags=>DB_CREATE, -Filename=>$dictionary_name{"feature_index"});
	tie(%dictionary_feature_ngram, "BerkeleyDB::Btree", -Flags=>DB_CREATE, -Filename=>$dictionary_name{"feature_ngram"});
}
#====================================================================
sub close_dictionary {
	untie(%dictionary_bitext);
	untie(%dictionary_ngram_count);

	untie(%dictionary_feature_map);
	untie(%dictionary_feature_index);

	untie(%dictionary_cluster);
	untie(%dictionary_cluster_feature);
}
#====================================================================
sub clean_dictionary {
	foreach my $db_name ( keys %dictionary_name ) {
		unlink($dictionary_name{$db_name}) if( -e $dictionary_name{$db_name} );
	}
}
#====================================================================
sub reset_cluster_dictionary {
	unlink($dictionary_name{"cluster"}) if( -e $dictionary_name{"cluster"} );
	unlink($dictionary_name{"cluster_feature"}) if( -e $dictionary_name{"cluster_feature"} );
	unlink($dictionary_name{"cluster_history"}) if( -e $dictionary_name{"cluster_history"} );
}
#====================================================================
sub report_cluster {
	my $n_cluster = scalar keys %dictionary_cluster;
	printf "# n cluster: %6d, %6d\n", $n_cluster, $dictionary_cluster{"_TOTAL_"};

	my $total_sentence = 0;
	my (%s_freq) = ();
	foreach my $c_id ( sort {$a<=>$b} keys %dictionary_cluster ) {
		next if( substr($c_id, 0, 1) eq "_" );

		my (%sub_cluster) = to_hash($dictionary_cluster{$c_id});

		my $cluster_size = scalar keys %sub_cluster;
		next if( $cluster_size < $args{"th_cluster_size"} );

		my (%features) = to_hash($dictionary_cluster_feature{$c_id});
		foreach my $s_id ( keys %sub_cluster ) {
			$s_freq{$s_id}++;
		}
		my $feature_size = scalar keys %features;

		# printf "# c:%05d\tn:%s\tf:%s\n", $c_id, comma($cluster_size), comma($feature_size);
		# printf "# %s\n", join("\t", keys %sub_cluster);
		printf "%6d\t%6d\n", $cluster_size, $c_id;

		$total_sentence += $cluster_size;
	}

	my $n_uniq = scalar keys %s_freq;
	my $avg_sentence = ( $n_uniq > 0 && $n_cluster > 0 ) ? $n_uniq/$n_cluster : 0;
	printf "# th_ngram: %3d, th_similarity: %f, total cluster : %s, total : %s, overlap : %s, unique : %s, avg. : %s\n", 
			$dictionary_cluster{"_TH_NAGRM_"},
			$dictionary_cluster{"_TH_SIMILARITY_"},
			comma($n_cluster), 
			comma($total_sentence), 
			comma($total_sentence - $n_uniq), 
			comma($n_uniq), 
			comma($avg_sentence);

	print_runtime((caller(0))[3]);
}
#====================================================================
sub print_runtime {
	my $func = shift(@_);

	return if( !defined($start_time) );
	printf STDERR "# func = %s, runtime = %.1f sec\n", $func, time - $start_time;
}
#====================================================================
sub convert_bitext_to_db {
	my $n_list = shift(@_);
	my $th_ngram_freq = shift(@_);

	my $sentence_id = 0;

	my (%buf_features) = ();
	while( my $line=<STDIN> ) {
		$line =~ s/^\s+|\s+$//g;
		$line =~ s/([.?!])$/ $1/;

		# print STDERR "$line\n";

		printf STDERR "." if( $sentence_id % 1000 == 0 );
		printf STDERR "(%s, %.1f sec)\n", comma($sentence_id), (time - $start_time) if( $sentence_id != 0 && $sentence_id % 100000 == 0 );

		my ($a, $b) = split(/\t/, $line);

		my (@token) = ();
		foreach my $sent ( split(/\t+/, $b) ) {
			push(@token, split(/\s+/, $sent));
		}

		$dictionary_bitext{$sentence_id} = $line;

		my (%features) = ();
		foreach my $n ( @{$n_list} ) {
			my (@ngram) = ();
			get_ngram(\@token, $n, \@ngram);

			foreach my $w ( @ngram ) {
				next if( !defined($dictionary_ngram_count{$w}) );

				next if( $dictionary_ngram_count{$w} < $th_ngram_freq );

		 		$features{$w} = 1;
		 		$buf_features{$w}{$sentence_id} = 1;
			}
		}

		$dictionary_feature_map{$sentence_id} = join("\t", sort keys %features);

		$sentence_id++;
	}

	$dictionary_bitext{"_TOTAL_"} = $sentence_id;

	printf STDERR "\n# total: %s, %.1f sec\n", comma($sentence_id), (time - $start_time);

	# update feature index
	printf STDERR "# update feature index\n";

	my $cnt = 0;
	my (%n_feature) = ();
	foreach my $w ( keys %buf_features ) {
		my (%uniq) = ();
		if( defined($dictionary_feature_index{$w}) ) {
			(%uniq) = to_hash($dictionary_feature_index{$w});
		}

		foreach my $id ( keys %{$buf_features{$w}} ) {
			$uniq{$id} = 1;
		}

		$n_feature{scalar split(/\s+/, $w)}{$w} = 1;

		$dictionary_feature_index{$w} = join("\t", sort keys %uniq);

		printf STDERR "." if( $cnt++ % 1000 == 0 );
		printf STDERR "(%s, %.1f sec)\n", comma($cnt), (time - $start_time) if( $cnt != 0 && $cnt % 100000 == 0 );
	}

	# update ngram size 
	foreach my $n ( keys %n_feature ) {
		$dictionary_feature_ngram{$n} = join("\t", sort keys %{$n_feature{$n}});
	}

	print_runtime((caller(0))[3]);
}
#====================================================================
sub read_bitext {
	my $df = shift(@_);
	my $doc = shift(@_);
	my $n_list = shift(@_);
	my $th_ngram_freq = shift(@_);

	my $features = shift(@_);
	my $features_index = shift(@_);
	my $features_index_len = shift(@_);

	my $d_count = 0;

	while( my $line=<STDIN> ) {
		$line =~ s/^\s+|\s+$//g;
		$line =~ s/([.?!])$/ $1/;

		# print STDERR "$line\n";

		printf STDERR "." if( $d_count % 100000 == 0 );
		printf STDERR "(%s)\n", comma($d_count) if( $d_count % 1000000 == 0 );

		my ($a, $b) = split(/\t/, $line);

		# push(@{$doc}, $b);

		# $b = lc($b);

		my (@token) = ();
		foreach my $sent ( split(/\t+/, $b) ) {
			push(@token, split(/\s+/, $sent));
		}

		foreach my $n ( @{$n_list} ) {
			my (@ngram) = ();
			get_ngram(\@token, $n, \@ngram);

			foreach my $w ( @ngram ) {
				next if( !defined($df->{$w}) );

				next if( $df->{$w} < $th_ngram_freq );

				$features->[$d_count]{$w}++;
				$features_index->{$w}{$d_count}++;
				$features_index_len->{$n}{$w} = 1;
			}
		}

		$d_count++;
	}

	printf STDERR "DONE: (%s)\n", comma($d_count);
	print_runtime((caller(0))[3]);

	return $d_count;
}
#====================================================================
sub get_feature_index {
	my (%feature_index) = ();

	foreach my $c_id ( keys %dictionary_cluster_feature ) {
		my (%feature) = to_hash($dictionary_cluster_feature{$c_id});

		foreach my $f ( keys %feature ) {
			$feature_index{$f}{$c_id} = 1;
		}
	}

	return (%feature_index);
}
#====================================================================
sub build_cluster {
	my $cluster_id = ( defined($dictionary_cluster{"_TOTAL_"}) ) ? $dictionary_cluster{"_TOTAL_"} : 0;
	return if( !defined($dictionary_feature_ngram{$args{"th_ngram"}}) );

	my (@cluster) = split(/\t/, $dictionary_feature_ngram{$args{"th_ngram"}});
	printf STDERR "# [%s] th_ngram=%6d, feature ngram=%6d, min_sentence=%6d\n", 
					(caller(0))[3],
					$args{"th_ngram"}, 
					scalar @cluster, 
					$args{"th_min_sentence"};

	my (%feature_index) = ();
	(%feature_index) = get_feature_index() if( $cluster_id > 0 );

	my $total_sentence = 0;
	my (%uniq_sentence) = ();
	
	foreach my $w ( @cluster ) {
		# big 1 feature => child sentence => n features
		my (%f_list) = ($w => 1);		
		(%f_list) = extend_feature($w, $args{"th_idf"}) if( !defined($args{"without_feature_extend"}) ); 

		my (@sentence_list) = get_sentence_list(\%f_list);

		my (%sub_cluster) = ();
		foreach my $s_id ( @sentence_list ) {
			$sub_cluster{$s_id} = 1;
		}

		# check minium sentence count
		my (@sub_cluster_keys) = keys %sub_cluster;
		my $cluster_size = scalar @sub_cluster_keys;

		next if( $cluster_size <= $args{"th_min_sentence"} );

		$total_sentence += $cluster_size;
		foreach my $s_id ( @sub_cluster_keys ) {
			$uniq_sentence{$s_id} = 1;
		}

		$dictionary_cluster{$cluster_id} = join("\t", @sub_cluster_keys);
		$dictionary_cluster_feature{$cluster_id} = join("\t", keys %f_list);

		if( defined($feature_index{$w}) ) {
			my $size = scalar keys %{$feature_index{$w}};
			if( $size == 1 ) {
				my ($prev_id) = keys %{$feature_index{$w}};

				merge_hash(\%dictionary_cluster, $prev_id, $cluster_id);
				merge_hash(\%dictionary_cluster_feature, $prev_id, $cluster_id);

				printf "# [%s] %6d => %6d\n", (caller(0))[3], $cluster_id, $prev_id;
				next;
			}
		}

		printf "# [%s] c_id:%6d, n_sentence:%6d:%6d, th_ngram:%6d, n_feature:%6d, ", 
					(caller(0))[3],
					$cluster_id, 
					scalar(@sentence_list), 
					scalar(@sub_cluster_keys), 
					$args{"th_ngram"}, 
					scalar(keys %f_list);
		# printf "\tfeature:%s", $w;
		printf "\n";

		$cluster_id++;
	}

	$dictionary_cluster{"_TOTAL_"} = $cluster_id;
	$dictionary_cluster_feature{"_TOTAL_"} = $cluster_id;

	save_cluster_status();
	my $uniq_sentence_size = scalar keys %uniq_sentence;
	printf "# [%s] n cluster: max=%d, n=%6d, th_ngram: %f, total: %s, uniq: %s, overlap: %s\n", 
			(caller(0))[3], 
			$cluster_id, 
			scalar keys %dictionary_cluster,
			$args{"th_ngram"},
			comma($total_sentence),
			comma($uniq_sentence_size),
			comma($total_sentence - $uniq_sentence_size);

	print_runtime((caller(0))[3]);
}
#====================================================================
sub extend_feature {
	my $w = shift(@_);
	my $th_idf = shift(@_);

	my (%ret) = ();

	my (@s_list) = split(/\t/, $dictionary_feature_index{$w});
	foreach my $s_id ( @s_list ) {
		my (%f_list) = to_hash($dictionary_feature_map{$s_id});

		foreach my $f ( keys %f_list ){
			my $idf = ( $dictionary_ngram_count{$f} > 0 ) ? log($total_sentence / $dictionary_ngram_count{$f}) : 0;

			# printf "# %s\t%d\t%.2f\n", $f, $total_sentence, $idf;
			next if( $idf <= $th_idf );

			$ret{$f} = 1;
		}
	}

	return (%ret);
}
#====================================================================
sub get_sentence_list {
	my $f_list = shift(@_);

	# printf "%d\t%f\t%d\n", $total_sentence, $th_idf, scalar(keys %{$f_list});

	my (%sentence_list) = ();
	foreach my $f ( keys %{$f_list} ) {
		my (%features) = to_hash($dictionary_feature_index{$f});
		foreach my $d ( keys %features ) {
			$sentence_list{$d} = 1;
		}
	}

	return (keys %sentence_list);
}
#====================================================================
sub merge_cluster_by_similarity {
	my $n_cluster = scalar keys %dictionary_cluster;
	printf STDERR "# th_similarity: %.2f, n cluster: %d, %d\n", $args{"th_similarity"}, $n_cluster, $dictionary_cluster{"_TOTAL_"};

	my (%sentence_similarity) = get_sentence_similarity($args{"th_similarity"}, $args{"th_cluster_size"});
	my $n_simiarity = scalar keys %sentence_similarity;

	printf STDERR "# similarity: n=%d, th=%.4f\n", $n_simiarity, $args{"th_similarity"};

	if( $n_simiarity > 0 ) {
		$n_cluster = merge_cluster(\%sentence_similarity, $args{"max_ncluster"});
		printf STDERR "# n cluster: %d\n", $n_cluster;
	}

	save_cluster_status();
	printf STDERR "# total_cluster: %d\n", scalar keys %dictionary_cluster;
}
#====================================================================
sub merge_cluster {
	my $sentence_similarity = shift(@_);
	my $max_ncluster = shift(@_);

	my $n_cluster = scalar keys %dictionary_cluster;
	printf "# [%s] similarity matrix size: %d\n", (caller(0))[3], scalar keys %{$sentence_similarity};

	my (%alias) = ();
	foreach my $sim ( sort {$b<=>$a} keys %{$sentence_similarity} ) {
		foreach my $c_a ( sort {$a<=>$b} keys %{$sentence_similarity->{$sim}} ) {
			my $id_a = $c_a;
			$id_a = $alias{$c_a} if( defined($alias{$c_a}) );

			next if( !defined($dictionary_cluster{$id_a}) );

			foreach my $c_b ( sort {$a<=>$b} keys %{$sentence_similarity->{$sim}{$c_a}} ) {
				my $id_b = $c_b;
				$id_b = $alias{$c_b} if( defined($alias{$c_b}) );

				next if( $id_a == $id_b );
				next if( !defined($dictionary_cluster{$id_b}) );

				printf "# merge: %6d\t%6d\t%f\n", $id_a, $id_b, $sim;

				# merge cluster & feature
				merge_hash(\%dictionary_cluster, $id_a, $id_b);
				merge_hash(\%dictionary_cluster_feature, $id_a, $id_b);

				$alias{$id_b} = $id_a;

				$n_cluster = scalar keys %dictionary_cluster;
				return $n_cluster if( $max_ncluster >= $n_cluster ); 
			}
		}
	}

	# uniq sentence number
	uniq_sentence_number(\%dictionary_cluster);
	uniq_sentence_number(\%dictionary_cluster_feature);

	$dictionary_cluster{"_TH_NAGRM_"} = $args{"th_ngram"};
	$dictionary_cluster{"_TH_SIMILARITY_"} = $args{"th_similarity"};

	print_runtime((caller(0))[3]);

	return $n_cluster;
}
#====================================================================
sub merge_hash {
	my $data = shift(@_);

	my $id_a = shift(@_);
	my $id_b = shift(@_);

	$data->{$id_a} = $data->{$id_a}."\t".$data->{$id_b};
	delete $data->{$id_b};
}
#====================================================================
sub uniq_sentence_number {
	my $data = shift(@_);

	foreach my $c_id ( keys %{$data} ) {
		my (%uniq) = to_hash($data->{$c_id});

		$data->{$c_id} = join("\t", keys %uniq);
	}

	my $i = 0;
	foreach my $c_id ( sort {$a<=>$b} keys %{$data} ) {
		if( $i < $c_id ){
			if( !defined($data->{$i}) ) {
				$data->{$i} = $data->{$c_id};
				delete $data->{$c_id};
			} else {
				printf STDERR "ERROR L:%d\n", __LINE__;
			}
		}

		$i++;
	}

	$data->{"_TOTAL_"} = $i;
	printf STDERR "# %s : %d\n", (caller(0))[3], $data->{"_TOTAL_"};
}
#====================================================================
sub to_hash {
	my $str_cluster = shift(@_);

	my (%ret) = ();
	foreach my $d ( split(/\t/, $str_cluster) ){
		next if( $d eq "" );

		$ret{$d} = 1;
	}

	return (%ret);
}
#====================================================================
sub to_list {
	my $str_cluster = shift(@_);

	return (split(/\t/, $str_cluster));
}
#====================================================================
sub get_sentence_similarity {
	my $th_similarity = shift(@_);
	my $th_cluster_size = shift(@_);

	my (%uniq) = ();
	my (%matrix) = ();

	my (@c_list) = sort {$a<=>$b} keys %dictionary_cluster;

	# (@c_list) = (1..5);

	printf STDERR "# c_list : %3d\n", scalar @c_list;

	# make cluster index
	my (%cluster, %cluster_list, %cluster_size) = ();
	foreach my $c_id ( @c_list ) {
		next if( substr($c_id, 0, 1) eq "_" );

		# my (@sub_cluster) = to_list($dictionary_cluster_feature{$c_id});
		my (@sub_cluster) = to_list($dictionary_cluster{$c_id});

		my $sub_cluster_size = scalar @sub_cluster;
		# next if( $th_cluster_size > $sub_cluster_size );

		foreach my $f ( @sub_cluster ) {
			$cluster{$c_id}{$f} = 1;
		}
		push(@{$cluster_list{$c_id}}, @sub_cluster);
		$cluster_size{$c_id} = $sub_cluster_size;
	}

	my (%removed_id) = ();
	foreach my $c_a ( @c_list ) {
		next if( substr($c_a, 0, 1) eq "_" );
		next if( defined($removed_id{$c_a}) );

		foreach my $c_b ( @c_list ) {	
			next if( substr($c_b, 0, 1) eq "_" );	
			next if( defined($removed_id{$c_b}) );

			next if( $c_a eq $c_b );
			next if( defined($uniq{$c_b}) );

			# printf "%d\t%d\n", $c_a, $c_b;

			my $comon = 0;
			foreach my $s ( @{$cluster_list{$c_a}} ) {
				$comon++ if( defined($cluster{$c_b}{$s}) );
			}

			my $sim = ( $comon > 0 ) ? ($comon * 2) / ($cluster_size{$c_a} + $cluster_size{$c_b}) : 0;

			$uniq{$c_a} = 1;

			if( $sim == 1 ) {
				merge_hash(\%dictionary_cluster, $c_a, $c_b);
				merge_hash(\%dictionary_cluster_feature, $c_a, $c_b);

				printf STDERR "# merge: %d <=> %d = %f\n", $c_a, $c_b, $sim;

				$removed_id{$c_b} = $c_a;

				my (@sub_cluster) = to_list($dictionary_cluster_feature{$c_a});
				foreach my $f ( @sub_cluster ) {
					$cluster{$c_a}{$f} = 1;
				}
				push(@{$cluster_list{$c_a}}, @sub_cluster);
				$cluster_size{$c_a} = @{$cluster_list{$c_a}};
			} elsif( $sim >= $th_similarity ) {
				$matrix{$sim}{$c_a}{$c_b} = 1;
				printf STDERR "# %6d <=> %6d = %.4f\n", $c_a, $c_b, $sim;
			}
		}
	}

	if( scalar keys %matrix > 0 ) {
		foreach my $sim ( keys %matrix ) {
			foreach my $c_id ( keys %{$matrix{$sim}} ) {
				next if( !defined($removed_id{$c_id}) );

				my $new_id = $removed_id{$c_id};
				foreach my $c_b ( keys %{$matrix{$sim}{$c_id}} ) {
					$matrix{$sim}{$new_id}{$c_b} = ( $matrix{$sim}{$new_id}{$c_b} + $matrix{$sim}{$c_id}{$c_b} ) / 2
				}

				delete $matrix{$sim}{$c_id};
			}
		}
	}

	print_runtime((caller(0))[3]);

	return (%matrix);
}
#====================================================================
sub get_feature_candidate {
	my $df = shift(@_);
	my $w_list = shift(@_);

	my $cnt = 0;
	foreach my $w ( keys %{$df} ) {
		# remove digit.
		next if( $w =~ m/^[0-9]+$/ );

		# remove single word
		next if( $w !~ m/ / );		

		$w_list->{$w} = $cnt++;
	}			
}
#====================================================================
sub get_ngram {
	my (@token) = (@{shift(@_)});
	my $n = shift(@_);
	my $ngram = shift(@_);

	$n--;

	return if( scalar(@token) < $n );	

	# <s> he have the car </s>
	unshift(@token, "<s>");
	push(@token, "</s>");

	for( my $i=0 ; $i<scalar(@token)-$n ; $i++ ) {
		my (@n_list) = @token[$i..($i+$n)];
		# next if( scalar(@n_list) < $n );

		my $stop = 0;
		for( my $j=0 ; $j<scalar(@n_list)-1 ; $j++ ) {
			if( defined($stop_word{$n_list[$j]}) ) {
				$stop = 1;
				last;
			}
		}
		next if( $stop == 1 );

		my $buf = join(" ", @n_list);

		# printf "$n: %s\n", $buf;

		$buf =~ s/\s+$//;
		$buf =~ s/^(<s> )+/<s> /;
		$buf =~ s/( <\/s>)+$/ <\/s>/;

		next if( $buf eq "" );

		push(@{$ngram}, $buf);
	}
}
#====================================================================
sub comma {
	my $cnt = shift(@_);

	$cnt = sprintf("%d", $cnt);
	for ( my $i = -3; $i > -1 * length($cnt); $i -= 4 ){
	    substr( $cnt, $i, 0 ) = ',';
	}

	return $cnt;
}
#====================================================================
sub remove_cluster_by_size {
	my (@cluster) = sort {$a<=>$b} keys %dictionary_cluster;

	my $n_cluster = scalar @cluster;
	printf STDERR "# n cluster: %d, %d\n", $n_cluster, $dictionary_cluster{"_TOTAL_"};

	my (@s_list) = get_cluster_size(@cluster);

	printf STDERR "# s_list: %d\n", scalar @s_list;

	return if( scalar @s_list <= 0 );

	for( my $i=0 ; $i<scalar(@s_list) ; $i++ ) {
		my $s_id = $s_list[$i];

		next if( !defined($dictionary_cluster{$s_id}) );

		my (@sub_cluster) = to_list($dictionary_cluster{$s_id});

		my $size = scalar @sub_cluster;
		delete $dictionary_cluster{$s_id};

		# my $n_cluster = scalar keys %dictionary_cluster;
		printf "# delete: c_id: %d\t size: %d\n", $s_id, $size;

		last if( $args{"max_ncluster"} >= $n_cluster ); 
	}

	# uniq sentence number
	uniq_sentence_number(\%dictionary_cluster);
	uniq_sentence_number(\%dictionary_cluster_feature);

	printf "# n_cluster: %d, %d\n", scalar keys %dictionary_cluster, $dictionary_cluster{"_TOTAL_"};

	print_runtime((caller(0))[3]);
}
#====================================================================
__END__


