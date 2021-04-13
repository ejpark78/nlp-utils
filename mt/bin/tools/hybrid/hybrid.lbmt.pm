#!/usr/bin/perl -w
#====================================================================
use strict;
#====================================================================
# SUB. FUNCTIONS
#====================================================================
sub make_hybrid_feature {
	my $json = shift(@_);
	my $line = shift(@_);
	my $db = shift(@_);

	my (%input) = ();
	my $decoded = $json->decode( $line );
	# print Dumper($decoded) if( $args{"debug"} );

	$input{"class"} = $decoded->{"class"};
	$input{"src"} = $decoded->{"source"};
	$input{"tst_smt"} = $decoded->{"smt"};
	$input{"tst_lbmt"} = $decoded->{"lbmt"};
	$input{"tagged_text"} = $decoded->{"tagged_text"};
	$input{"phrase_log"} = $decoded->{"phrase_log"};

	# foreach my $k ( keys %input ) {
	# 	printf STDERR "# %s => %s\n", $k, $input{$k};
	# }

	my (@sent) = (@{$input{"phrase_log"}});
	my (%features) = ();

	phrase_prob($db, "ko", "cn", \@sent, \%features);
	$features{"lex_prob_smt"} = lex_prob($db, $input{"src"}, $input{"tst_smt"});
	$features{"lex_prob_lbmt"} = lex_prob($db, $input{"src"}, $input{"tst_lbmt"});
	lm_score($db->{"lm_f"}, $db->{"lm_backoff_f"}, $input{"src"}, \%features, "src");
	lm_score($db->{"lm_f"}, $db->{"lm_backoff_f"}, $input{"tst_smt"}, \%features, "smt");
	lm_score($db->{"lm_f"}, $db->{"lm_backoff_f"}, $input{"tst_lbmt"}, \%features, "lbmt");
	get_pos_features($input{"tagged_text"}, \%features);
	get_feature_diff(\%input, \%features);

	my $i=1;
	my (@result) = ();
	foreach my $k ( qw/ 
			diff_len_src-lbmt diff_len_src-lbmt_rate diff_len_src-smt diff_len_src-smt_rate diff_len_tst diff_lm-common-n1 diff_lm-common-n2 diff_lm-common-n3 diff_lm-common-n4 diff_lm-common-n5 diff_lm-lbmt-n1 diff_lm-lbmt-n2 diff_lm-lbmt-n3 diff_lm-lbmt-n4 diff_lm-lbmt-n5 diff_lm-smt-n1 diff_lm-smt-n2 diff_lm-smt-n3 diff_lm-smt-n4 diff_lm-smt-n5 
			lbmt_lm-n1 lbmt_lm-n2 lbmt_lm-n3 lbmt_lm-n4 lbmt_lm-n5 
			lex_prob_lbmt lex_prob_smt 
			lm_e lm_f 
			phrase phrase_prob 
			pos_E pos_J pos_N pos_S pos_V 
			smt_lm-n1 smt_lm-n2 smt_lm-n3 smt_lm-n4 smt_lm-n5 
			src_lm-n1 src_lm-n2 src_lm-n3 src_lm-n4 src_lm-n5 
			tok_e tok_f 
			token_lbmt token_smt 
			unk / ) {			
		
		# push(@result, sprintf("%d:%s", $i++, $features{$k}));
		push(@result, $features{$k});
	}

	$input{"class"} = 1 if( !defined($input{"class"}) );

	return (\%input, \@result, \%features);
}
#====================================================================
sub get_feature_diff {
	my (%data) = (%{shift(@_)});
	my $features = shift(@_);

	my (@token_src) = split(/\s+/, $data{"source"});
	my (@token_tst1) = split(/\s+/, $data{"smt"});
	my (@token_tst2) = split(/\s+/, $data{"lbmt"});

	for( my $i=1 ; $i<=5 ; $i++ ) {
		$features->{"diff_lm-smt-n$i"} = ($features->{"src_lm-n$i"} - $features->{"smt_lm-n$i"});
		$features->{"diff_lm-lbmt-n$i"} = ($features->{"src_lm-n$i"} - $features->{"lbmt_lm-n$i"});
		$features->{"diff_lm-common-n$i"} = ($features->{"smt_lm-n$i"} - $features->{"lbmt_lm-n$i"});
	}

	$features->{"diff_len_tst"} = scalar(@token_tst1) - scalar(@token_tst2);

	$features->{"diff_len_src-smt"} = scalar(@token_src) - scalar(@token_tst1);
	$features->{"diff_len_src-smt_rate"} = ( $features->{"diff_len_src-smt"} > 0 ) ? scalar(@token_tst1) / $features->{"diff_len_src-smt"} : 0;

	$features->{"diff_len_src-lbmt"} = scalar(@token_src) - scalar(@token_tst2);
	$features->{"diff_len_src-lbmt_rate"} = ( $features->{"diff_len_src-lbmt"} > 0 ) ? scalar(@token_tst2) / $features->{"diff_len_src-lbmt"} : 0;

	$features->{"token_smt"} = scalar(@token_tst1);
	$features->{"token_lbmt"} = scalar(@token_tst2);
}
#====================================================================
sub get_pos_features {
	my $text = shift(@_);
	my $features = shift(@_);

	my (@token_pos) = split(/\s+/, $text);

	my (%pos_count) = ("V" => 0, "E" => 0, "N" => 0, "J" => 0, "X" => 0, "M" => 0);
	foreach my $word ( @token_pos ) {
		my ($w, $p) = split(/\//, $word, 2);
		$p =~ s/^(.).+$/$1/g;
		$features->{"pos_".$p}++;
	}
}
#====================================================================
sub lm_score {
	my $lm_db = shift(@_);
	my $backoff_db = shift(@_);
	my $text = shift(@_);
	my $features = shift(@_);
	my $tag = shift(@_);

	my (%ngram) = ();

	my (@token) = split(/\s+/, $text);

	my (%ngram, %lm_score, %buf_log) = ();

	get_lm_candidate(\@token, 1, \@{$ngram{"n1"}});
	($lm_score{"n1"}, $buf_log{"n1"}) = get_lm_score($lm_db, $backoff_db, 1, \@{$ngram{"n1"}});

	get_lm_candidate(\@token, 2, \@{$ngram{"n2"}});
	($lm_score{"n2"}, $buf_log{"n2"}) = get_lm_score($lm_db, $backoff_db, 2, \@{$ngram{"n2"}});

	get_lm_candidate(\@token, 3, \@{$ngram{"n3"}});
	($lm_score{"n3"}, $buf_log{"n3"}) = get_lm_score($lm_db, $backoff_db, 3, \@{$ngram{"n3"}});

	get_lm_candidate(\@token, 4, \@{$ngram{"n4"}});
	($lm_score{"n4"}, $buf_log{"n4"}) = get_lm_score($lm_db, $backoff_db, 4, \@{$ngram{"n4"}});

	get_lm_candidate(\@token, 5, \@{$ngram{"n5"}});
	($lm_score{"n5"}, $buf_log{"n5"}) = get_lm_score($lm_db, $backoff_db, 5, \@{$ngram{"n5"}});

	foreach my $k ( sort keys %lm_score ) {
		my $log = "";
		$log = join(", ", @{$buf_log{$k}}) if( defined($buf_log{$k}) );

		$features->{$tag."_lm-".$k} = 2**(-$lm_score{$k});
	}
}
#====================================================================
sub get_lm_score
{
	my $lm_db = shift(@_);
	my $backoff_db = shift(@_);
	my $n = shift(@_);
	my (@lm_candidate) = @{shift(@_)};

	my $nosmoothing = 0;
	# $nosmoothing = 1;

	my ($lm_score) = (0);
	my (%ret) = ();

	foreach my $np_pos ( @lm_candidate ) {
		# without pos tag
		my $np = $np_pos;
		$np =~ s/\/[A-Z]+?/ /g;

		next if( !defined($lm_db) );

		if( defined($lm_db->Get($np)) ) {
			my $score = $lm_db->Get($np);

			$lm_score += $score;
			$ret{$np} += $score;
			next;
		} 

		# ignore smoothing
		if( $nosmoothing ) {
			my $score = log(1/10000000000);
			$lm_score += $score;
			$ret{$np} += $score;
			# printf ">>>>$np:>%.f\n", log(1/10000000000);
			next;
		}

		# backoff - KneserNey
		my $score_backoff = get_backoff($lm_db, $backoff_db, $np);

		$ret{$np} += $score_backoff;
		$lm_score += $score_backoff;
	}

	my (@buf) = ();
	foreach my $k ( sort keys %ret ) { 
		push(@buf, "p($k, $ret{$k})");
	}

	my $ret_score = $lm_score;
	$ret_score = $lm_score / scalar(@buf) if( scalar(@buf) > 0 );

	# if( $args{"debug"} ) {
	# 	print STDERR "\n# summary\n";

	# 	print STDERR "# p(".join(" | ", @lm_candidate).") ~= \n";
	# 	print STDERR "# ".join("\n# + ", @buf);
	# 	print STDERR "\n# ~= perplexity= ".(2**(-$ret_score)).", log(p)=$ret_score, ($lm_score / ".scalar(@buf).")";
	# 	print STDERR ", ".POSIX::pow(2, $lm_score)."\n\n";
	# }

	# return POSIX::pow(2, $lm_score);
	return ($ret_score, \@buf);
}
#====================================================================
sub get_backoff
{	
	my $lm_db = shift(@_);
	my $backoff_db = shift(@_);
	my $np = shift(@_);

	# print STDERR "\n# get_backoff\n" if( $args{"debug"} );

	my $score_backoff = 0;
	my (@backoff_log) = ();

	my $needle = $np;
	$needle =~ s/^[ ]+ //;

	# $ret{$needle} += 0;
	if( defined($lm_db->Get($needle)) ) {
		my $score = $lm_db->Get($needle);

		$score_backoff += $score;
		push(@backoff_log, "p($needle, $score)");

		# printf STDERR "# \t%s\n", join("+", @backoff_log) if( $args{"debug"} );

		return $score_backoff;
	}

	# p(a b c) = p(c) + b(b) + b(a b)
	# p(d | a b c) = p(d) + b(c) + b(b c) + b(a b c)
	# b( so | i love you) = p(so) + b(you) + b(love you) + b(i love you)

	return $score_backoff if( !defined($backoff_db) );

	my (@token_np) = split(/ /, $np);
	$needle = pop(@token_np);

	if( $needle ne "</s>" ) {
		if( defined($lm_db->Get($needle)) ) {
			my $score = $lm_db->Get($needle);

			$score_backoff += $score;
			push(@backoff_log, "p($needle, $score)");
		} else {
			push(@backoff_log, "p($needle, null)");			
		}
	}

	for( my $i=0 ; $i<scalar(@token_np) ; $i++ ) {
		$needle = join(" ", @token_np[($#token_np-$i)..$#token_np]);

		next if( $needle eq "<s>" || $needle eq "</s>" );

		if( !defined($backoff_db->Get($needle)) ) {
			push(@backoff_log, "b($needle, null)");			
			next;
		}

		my $score = $backoff_db->Get($needle);
		
		$score_backoff += $score;			
		push(@backoff_log, "b($needle, $score)");			
	}

	# printf STDERR "# \tp(%s) := %f, %s\n", $np, $score_backoff, join(" + ", @backoff_log) if( $args{"debug"} );

	# return $score_backoff/scalar(@backoff_log);
	return $score_backoff;
}
#====================================================================
sub lex_prob {
	my (%db) = (%{shift(@_)});
	my $src = shift(@_);
	my $tst = shift(@_);
	my $features = shift(@_);

	my (@token_src) = split(/\s+/, $src);
	my (@token_tst) = split(/\s+/, $tst);

	my (%ngram_src, %ngram_tst, %ngram_ref) = ();
	get_ngram(\@token_src, 1, \@{$ngram_src{"n1"}});
	get_ngram(\@token_tst, 1, \@{$ngram_tst{"n1"}});

	my (%tst, %ref) = ();
	foreach my $f ( @{$ngram_src{"n1"}} ) {
		get_align_prob($f, $db{"lex"}, \@{$ngram_tst{"n1"}}, \%tst);
	}

	$tst{"perplexity"} = $ref{"perplexity"} = 0;
	$tst{"perplexity"} = 2**(-$tst{"sum"}/$tst{"cnt"}) if( $tst{"cnt"} > 0 );

	return $tst{"perplexity"}; 	
}
#====================================================================
sub phrase_prob {
	my (%db) = (%{shift(@_)});
	my ($src_tag) = shift(@_);
	my ($trg_tag) = shift(@_);
	my (@sent) = (@{shift(@_)});
	my $features = shift(@_);

	# seek phrase-table
	my (%cnt) = ("unk" => 0);
	my ($align) = ();
	my (%sum, %buf) = ();
	foreach( @sent ) {
		my (%phrase) = (%{$_});

		my $f = $phrase{$src_tag};
		my $e = $phrase{$trg_tag};
		my (%align) = get_align_info($phrase{"align"});

		$cnt{"unk"}++ if( $e =~ /\|UNK/i );
		$cnt{"phrase"}++;

		# printf STDERR "# f = $f, e = $e, align = %s\n", $phrase{"align"} if( $args{"debug"} );

		$e =~ s/\|UNK//g;

		my (@tok_f) = split(/\s+/, $f);
		my (@tok_e) = split(/\s+/, $e);

		$cnt{"tok_f"} += scalar(@tok_f);
		$cnt{"tok_e"} += scalar(@tok_e);

		# compute word align prob.
		foreach my $i ( sort keys %align ) {
			foreach my $j ( sort keys %{$align{$i}} ) {
				my $score = $db{"lex"}->Get($tok_f[$i].":".$tok_e[$j]);
				# printf STDERR "# align: $i-$j\t%s\t%s\t%f\n", $tok_f[$i], $tok_e[$j], $score if( $args{"debug"} );

				$score = 0.00000001 if( $score == 0 );

				$cnt{"align"}++;
				$sum{"align"} += log($score);
			}
		}

		# compute phrase prob.
		if( defined($db{"phrase_prob"}) ) {
			my ($score, $polymorphism) = get_phrase_prob($f, $db{"phrase_prob"}->Get($f), $e);
			if( $score == 0 ) {
				$score = 0.0001;
				$polymorphism = 1;
			}

			# type 1
			$cnt{"phrase_prob"}++;
			$sum{"phrase_prob"} += log($score);

			push(@{$buf{"phrase_prob"}}, sprintf("p($f, $e, %f)", $score));

			# type 2
			$cnt{"phrase_prob2"}++;
			$sum{"phrase_prob2"} += log($score) + log(1/$polymorphism);

			push(@{$buf{"phrase_prob2"}}, sprintf("p($f, $e, %f, %d)", $score, $polymorphism));
		} 

		# compute phrase lm score
		if( defined($db{"lm_f"}) ) {
			my $score = $db{"lm_f"}->Get($f);
			$score = -10  if( !defined($score) || $score eq "" );	

			# type 1
			$cnt{"lm_f"}++;
			$sum{"lm_f"} += $score;

			push(@{$buf{"lm_f"}}, sprintf("p($f, %f)", $score));
		}

		if( defined($db{"lm_e"}) ) {
			my $score = $db{"lm_e"}->Get($e);
			$score = -10  if( !defined($score) || $score eq "" );	

			# type 1
			$cnt{"lm_e"}++;
			$sum{"lm_e"} += $score;

			push(@{$buf{"lm_e"}}, sprintf("p($f, %f)", $score));
		}
	}

	(@sent) = ();

	foreach my $k ( qw/ phrase unk tok_f tok_e / ) {
		next if( !defined($cnt{$k}) );

		$features->{$k} = $cnt{$k};
		# printf STDERR "($k:%d)\t", $cnt{$k} if( $args{"debug"} );
	}

	my $flag = 0;
	foreach my $k ( qw/ align lm_f lm_e phrase_prob / ) {
		next if( !defined($sum{$k}) );
		
		$flag = 1;

		$features->{$k} = 2**(-$sum{$k}/$cnt{$k});
		# printf STDERR "($k:%f/%d)\t", $sum{$k}, $cnt{$k} if( $args{"debug"} );
	}

	# printf STDERR "\n" if( $args{"debug"} );
}
#====================================================================
sub get_lm_candidate
{
	my (@token) = (@{shift(@_)});
	my $n = shift(@_);
	my $ret = shift(@_);

	$n--;

	# <s> he have the car </s>

	for( my $i=0 ; $i<scalar($n) ; $i++ ) {
		unshift(@token, "<s>");
		push(@token, "</s>");
	}

	my (%count) = ("total" => 0, "v" => 0, "token_v" => 0);
	foreach my $w ( @token ) {
		$count{"token_v"} ++ if( $w =~ /\/V/i );
	}

	for( my $i=0 ; $i<scalar(@token)-$n ; $i++ ) {
		my $buf = join(" ", @token[$i..($i+$n)]);

		$buf =~ s/\s+$//;
		$buf =~ s/^(<s> )+/<s> /;
		$buf =~ s/( <\/s>)+$/ <\/s>/;

		next if( $buf eq "" );

		push(@{$ret}, $buf);

		$count{"total"}++;
		$count{"v"}++ if( $buf =~ /\/V/i );
	}

	# if( $args{"debug"} ) {
	# 	print STDERR "\n";
	# 	print STDERR "### get_lm_candidate: n=$n\n";
	# 	print STDERR "# input token (n: $n): ".join(" ", @token)."\n";
	# 	print STDERR "# ngram list: (".scalar(@{$ret}).") ".join(" ||| ", @{$ret})."\n";
	# }

	$count{"token"} = scalar(@token);
	$count{"total"} = -1 if( $count{"total"} == 0 );

	return (%count);
}
#====================================================================
sub get_align_prob
{
	my $f = shift(@_);
	my $lex_db = shift(@_);
	my (@ngram) = (@{shift(@_)});
	my $sent_prob = shift(@_);

	my (%prob, %dict) = ();
	foreach my $e ( @ngram ) {
		my $k = "$f:$e";
		if( defined($lex_db->Get($k)) && $prob{$f} < $lex_db->Get($k) ) {
			$dict{$f} = $k;
			$prob{$f} = $lex_db->Get($k);
		}
	}

	foreach my $f ( keys %prob ) {
		$sent_prob->{"cnt"}++;
		$sent_prob->{"sum"} += log($prob{$f});
		# print STDERR "# $f ($dict{$f}) := $prob{$f}\n" if( $args{"debug"} );
	}
}
#====================================================================
sub get_ngram
{
	my (@token) = (@{shift(@_)});
	my $n = shift(@_);
	my $ret = shift(@_);

	$n--;

	# <s> he have the car </s>

	for( my $i=0 ; $i<scalar($n) ; $i++ ) {
		unshift(@token, "<s>");
		push(@token, "</s>");
	}

	my (%count) = ("total" => 0, "v" => 0, "token_v" => 0);
	foreach my $w ( @token ) {
		$count{"token_v"} ++ if( $w =~ /\/V/i );
	}

	for( my $i=0 ; $i<scalar(@token)-$n ; $i++ ) {
		my $buf = join(" ", @token[$i..($i+$n)]);

		$buf =~ s/\s+$//;
		$buf =~ s/^(<s> )+/<s> /;
		$buf =~ s/( <\/s>)+$/ <\/s>/;

		next if( $buf eq "" );

		push(@{$ret}, $buf);

		$count{"total"}++;
		$count{"v"}++ if( $buf =~ /\/V/i );
	}

	# if( $args{"debug"} ) {
	# 	print STDERR "\n";
	# 	print STDERR "### get_ngram: n=$n\n";
	# 	print STDERR "# input token (n: $n): ".join(" ", @token)."\n";
	# 	print STDERR "# ngram list: (".scalar(@{$ret}).") ".join(" ||| ", @{$ret})."\n";
	# }

	$count{"token"} = scalar(@token);
	$count{"total"} = -1 if( $count{"total"} == 0 );

	return (%count);
}
#====================================================================
sub get_align_info
{
	my $align = shift(@_);

	my (%ret) = ();

	foreach( split(/\s+/, $align) ) {
		my ($f, $e) = split(/-/, $_, 2);
		$ret{$f}{$e} = 1;
	}

	return (%ret);
}
#====================================================================
sub get_phrase_lm 
{
	my $lm = shift(@_);
	my $phrase = shift(@_);

	my (@token) = split(/\s+/, $phrase);

	# p(통하 지 않 는다) => p( 는다 | 통하 지 않 ) * p( 않 | 통하 지 ) * p( 지 | 통하 ) * p(통하)

	my $ret = 0;

	# print STDERR "# $phrase\n" if( $args{"debug"} );
	for( my $i=0 ; $i<scalar(@token) ; $i++ ) {
		my $needle = join(" ", @token[0..($#token-$i)]);

		if( !defined($lm->Get($needle)) ) {
			# print STDERR "p($needle, null)\n" if( $args{"debug"} );
			next;
		}

		my $score = $lm->Get($needle);
		# print STDERR "p($needle, $score)\n" if( $args{"debug"} );

		$ret += $score if( defined($score) && $score ne "" );
	}
	# print STDERR "# $phrase: $ret\n\n" if( $args{"debug"} );

	return $ret;
}
#====================================================================
sub get_phrase_prob 
{
	my $k = shift(@_);
	my $phrase_v = shift(@_);
	my $phrase = shift(@_);

	$phrase_v = decode('UTF-8', $phrase_v, Encode::FB_CROAK);

	my (@token) = split(/ \|\|\| /, $phrase_v);

	# printf STDERR "# $k => [$phrase] := [%s]\n", join(", ", @token) if( $args{"debug"} );

	my $probability = 0;
	foreach my $unit ( @token ) {
		my ($v, $p) = split(/\t/, $unit);

		next if( $v ne $phrase );

		$probability = $p;
		last;
	}

	my $sum = 0;
	foreach my $unit ( @token ) {
		my ($v, $p) = split(/\t/, $unit);
		$sum += $p;
	}

	# printf STDERR "# $k => [$sum]\n" if( $args{"debug"} );

	return ($probability, scalar(@token));
}
#====================================================================
sub parse_sequence {
	my $sequence = shift(@_);

	my $idx = 0;
	my (%input_sequence) = ();
	foreach my $pos ( split(/,/, $sequence) ) {
		$input_sequence{$pos} = $idx;
		$idx++;
	}

	return (%input_sequence);
}
#====================================================================
sub init_svm {
	my $log_dir = shift(@_);
	my $pid = shift(@_);

	my $cmd = "";
	$cmd = "svm-predict";
	$cmd .= " /dev/stdin";
	$cmd .= " /home/ejpark/workspace/model/hybrid/model/train-02.bleu-0.65.model";
	$cmd .= " /dev/stdout";
	$cmd .= " 2>> $log_dir/svm.log" if( -d $log_dir );

	$pid->{"svm"} = open2(*STDOUT_SVM, *STDIN_SVM, $cmd);

	binmode(STDIN_SVM, ":encoding(utf8)");
	binmode(STDOUT_SVM, ":encoding(utf8)");

	STDIN_SVM->autoflush(1);
	STDOUT_SVM->autoflush(1);

	return (\*STDIN_SVM, \*STDOUT_SVM);
}
#====================================================================
sub init_svm_scale {
	my $log_dir = shift(@_);
	my $pid = shift(@_);

	my $cmd = "";
	$cmd = "svm-scale -l 0 -u 1 /dev/stdin";
	$cmd .= " 2>> $log_dir/svm_scale.log" if( -d $log_dir );

	$pid->{"svm"} = open2(*STDOUT_SVM_SCALE, *STDIN_SVM_SCALE, $cmd);

	binmode(STDIN_SVM_SCALE, ":encoding(utf8)");
	binmode(STDOUT_SVM_SCALE, ":encoding(utf8)");

	STDIN_SVM_SCALE->autoflush(1);
	STDOUT_SVM_SCALE->autoflush(1);

	return (\*STDIN_SVM_SCALE, \*STDOUT_SVM_SCALE);
}
#====================================================================
sub init_smt {
	my $log_dir = shift(@_);
	my $pid = shift(@_);

	my $cmd = "";
	$cmd = "moses";
	$cmd .= " -translation-details /dev/stderr";
	# $cmd .= " -f /home/ejpark/workspace/model/ko-cn/tm-200.exclude/moses.memory.ini";
	$cmd .= " -f /home/ejpark/workspace/model/ko-cn/tm-200.exclude/moses.binary.ini";

	$pid->{"smt"} = open3(*STDIN_SMT, *STDOUT_SMT, *STDERR_SMT, $cmd);

	binmode(STDIN_SMT, ":encoding(utf8)");
	binmode(STDOUT_SMT, ":encoding(utf8)");
	binmode(STDERR_SMT, ":encoding(utf8)");

	STDIN_SMT->autoflush(1);
	STDOUT_SMT->autoflush(1);
	STDERR_SMT->autoflush(1);

	return (\*STDIN_SMT, \*STDOUT_SMT, \*STDERR_SMT);
}
#====================================================================
sub init_segmenter_cn {
	my $log_dir = shift(@_);
	my $pid = shift(@_);

	my $cmd = "";

	my $segmenter = "/home/ejpark/tools/stanford-segmenter-2013-06-20";
	$cmd = "java -mx2g -cp \"$segmenter/seg.jar\" edu.stanford.nlp.ie.crf.CRFClassifier";
	$cmd .= " -sighanCorporaDict \"$segmenter/data\"";
	$cmd .= " -readStdin";
	$cmd .= " -inputEncoding UTF-8";
	$cmd .= " -sighanPostProcessing true";
	$cmd .= " -keepAllWhitespaces false";
	$cmd .= " -loadClassifier \"$segmenter/data/ctb.gz\"";
	$cmd .= " -serDictionary \"$segmenter/data/dict-chris6.ser.gz\"";
	$cmd .= " -sentenceDelimiter newline -tokenize true";
	$cmd .= " 2>> $log_dir/segmenter_cn.log" if( -d $log_dir );

	$pid->{"segmenter_cn"} = open2(*STDOUT_SEGMENTER_CN, *STDIN_SEGMENTER_CN, $cmd);

	binmode(STDIN_SEGMENTER_CN, ":encoding(utf8)");
	binmode(STDOUT_SEGMENTER_CN, ":encoding(utf8)");

	STDIN_SEGMENTER_CN->autoflush(1);
	STDOUT_SEGMENTER_CN->autoflush(1);

	return (\*STDIN_SEGMENTER_CN, \*STDOUT_SEGMENTER_CN);
}
#====================================================================
sub init_mlt_kc {
	my $log_dir = shift(@_);
	my $pid = shift(@_);

	my $cmd = "";
	$cmd = "/home/ejpark/tools/LBMT/mlt_kc";
	$cmd .= " -cmd STDIN_TRANS";
	$cmd .= " -conf /home/ejpark/tools/LBMT/config_kc.0.ini";
	$cmd .= " 2>> $log_dir/mlt_kc.log" if( -d $log_dir );

	$pid->{"mlt_kc"} = open2(*STDOUT_MLT_KC, *STDIN_MLT_KC, $cmd);

	binmode(STDIN_MLT_KC, ":encoding(utf8)");
	binmode(STDOUT_MLT_KC, ":encoding(utf8)");

	STDIN_MLT_KC->autoflush(1);
	STDOUT_MLT_KC->autoflush(1);

	return (\*STDIN_MLT_KC, \*STDOUT_MLT_KC);
}
#====================================================================
sub init_tagging_ko {
	my $log_dir = shift(@_);
	my $pid = shift(@_);

	my $cmd = "";
	$cmd = "/home/ejpark/tools/bin/tagging_ko";
	$cmd .= " /home/ejpark/workspace/model/tagger/ko/model.syllpostagger.ap.crfsuite";
	$cmd .= " 2>> $log_dir/tagging_ko.log" if( -d $log_dir );

	$pid->{"tagging_ko"} = open2(*STDOUT_TAGGING_KO, *STDIN_TAGGING_KO, $cmd);

	binmode(STDIN_TAGGING_KO, ":encoding(utf8)");
	binmode(STDOUT_TAGGING_KO, ":encoding(utf8)");

	STDIN_TAGGING_KO->autoflush(1);
	STDOUT_TAGGING_KO->autoflush(1);

	return (\*STDIN_TAGGING_KO, \*STDOUT_TAGGING_KO);
}
#====================================================================
sub translate_smt {
	my $url = shift(@_);
	my $text = shift(@_);
	my $src_tag = shift(@_);
	my $trg_tag = shift(@_);

	my $proxy = XMLRPC::Lite->proxy($url);
	my $encoded = SOAP::Data->type("string" => $text);

	my %param = ("text" => $encoded, "align" => "true", "report-all-factors" => "true");
	my $result = $proxy->call("translate", \%param)->result;

	my (@src) = split(/\s+/, $text);
	my (@trg) = split(/\s+/, $result->{"text"});

	my (@phrase_log) = ();

	if( $result->{"align"} ) {
	    my $aligns = $result->{"align"};

		my $i = 0;
		my $tgt_start = -1;
		my (@buf) = ();
	    foreach my $align (@$aligns) {
			(@buf) = ();
			for( my $j=$align->{"src-start"} ; $j<=$align->{"src-end"} ; $j++ ) {
				push(@buf, $src[$j]);
			}
			$phrase_log[$i]{$src_tag} = join(" ", @buf);

			if( $tgt_start >= 0 ) {
				(@buf) = ();
				for( my $j=$tgt_start ; $j<$align->{"tgt-start"} ; $j++ ) {
					push(@buf, $trg[$j]);
				}
				$phrase_log[$i-1]{$trg_tag} = join(" ", @buf);
			}
			$tgt_start = $align->{"tgt-start"};

			$i++;
	    }

		(@buf) = ();
		for( my $j=$tgt_start ; $j<scalar(@trg) ; $j++ ) {
			push(@buf, $trg[$j]);
		}
		$phrase_log[$i-1]{$trg_tag} = join(" ", @buf);

		# foreach( my $i=0 ; $i<scalar(@phrase_log) ; $i++ ) {
		# 	printf "%s => %s\n", $phrase_log[$i]{$src_tag}, $phrase_log[$i]{$trg_tag};
		# }
	}

	return ($result->{"text"}, @phrase_log);
}
#====================================================================
sub safesystem {
	print STDERR "Executing: @_\n";

	system(@_);

	if ($? == -1) {
		print STDERR "Failed to execute: @_\n  $!\n";
		exit(1);
	} elsif ($? & 127) {
		printf STDERR "Execution of: @_\n  died with signal %d, %s coredump\n", ($? & 127),  ($? & 128) ? 'with' : 'without';
		exit(1);
	}
	else {
		my $exitcode = $? >> 8;
		print STDERR "Exit code: $exitcode\n" if $exitcode;
		return ! $exitcode;
	}
}
#====================================================================

1

__END__
