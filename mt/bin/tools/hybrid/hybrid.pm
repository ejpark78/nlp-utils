#!/usr/bin/perl -w
#====================================================================
use strict;
#====================================================================
# SUB. FUNCTIONS
#====================================================================
our $_debug = 1;
#====================================================================
sub parse_hybrid_class {
	my $class = shift(@_);

	# tm-2M:-1,drama-2.9M:0,movies-3.2M:1

	my (%ret) = ();
	foreach my $item ( split(/,/, $class) ) {
		my ($m, $c) = split(/:/, $item, 2);

		$ret{$m} = $c;
	}

	return (%ret);
}
#====================================================================
sub get_class_name {
	my $class = shift(@_);

	my (%model) = parse_hybrid_class($class);

	my (%ret) = ();

	foreach my $m ( keys %model ) {
		$ret{ $model{$m} } = $m;
	}

	return (%ret);
}
#====================================================================
sub make_hybrid_feature {
	my $json = shift(@_);
	my $line = shift(@_);
	my $db = shift(@_);

	my (%input) = ();
	my $decoded = $json->decode( $line );
	# print STDERR Dumper($decoded) if( $_debug );

	$input{"src"} = $decoded->{"source"};
	$input{"src_pos"} = $decoded->{"source_pos"};

	foreach my $m ( keys %{$db} ) {
		$input{$m}{"tst"} 	= $decoded->{"$m:model"};
		$input{$m}{"detail"}= $decoded->{"$m:detail"};
		$input{$m}{"bleu"} 	= $decoded->{"$m:bleu"};
		$input{$m}{"nist"} 	= $decoded->{"$m:nist"};
	}

	my (%features) = ();

	get_pos_features($input{"src_pos"}, \%{$features{"src"}});

	my (@model_list) = (sort keys %{$db});

	foreach my $m ( @model_list ) {	
		my (@sent) = (@{$input{$m}{"detail"}});

		foreach my $m2 ( @model_list ) {	
			phrase_prob($db->{$m2}, "ko", "en", \@sent, \%{$features{"$m:$m2"}});

			$features{"$m:$m2"}{"prob:lex"} = lex_prob($db->{$m2}, $input{"src"}, $input{$m}{"tst"});

			lm_score($db->{$m2}{"f_lm"}, $db->{$m2}{"f_lm_backoff"},
					$input{"src"}, \%{$features{"$m:$m2"}}, "src");
			lm_score($db->{$m2}{"f_lm"}, $db->{$m2}{"f_lm_backoff"},
					$input{$m}{"tst"}, \%{$features{"$m:$m2"}}, "tst");
		
			get_lm_diff($input{"src"}, $input{$m}{"tst"}, \%{$features{"$m:$m2"}});
		}
	}

	return (\%input, \%features);
}
#====================================================================
sub get_class {
	my (%model) = (%{shift(@_)});
	my (%input) = (%{shift(@_)});
	my ($features) = shift(@_);

	my (@value) = keys(%model);
	my $class = shift(@value);

	my $bleu = -1;
	foreach my $m ( keys %model ) {
		next if( !defined($input{$m}{"bleu"}) );

		if( $bleu < $input{$m}{"bleu"} ) {
			$bleu = $input{$m}{"bleu"};
			$class = $m;
		}
	}

	return $class;
}
#====================================================================
sub get_lm_diff {
	my $src = shift(@_);
	my $tst = shift(@_);
	my $features = shift(@_);

	my (@token_src) = split(/\s+/, $src);
	my (@token_tst) = split(/\s+/, $tst);

	for( my $i=1 ; $i<=5 ; $i++ ) {
		$features->{"lm:diff:$i"} = ($features->{"lm:src:$i"} - $features->{"lm:tst:$i"});
	}

	use Try::Tiny;
	
	try {
		$features->{"diff:token"} = scalar(@token_src) - scalar(@token_tst);
		$features->{"diff:length:rate"} = ( $features->{"diff:token"} > 0 ) ? $features->{"diff:token"} / scalar(@token_tst) : 0;
	} catch {
		print STDERR "ERROR ($_): src: [$src], tst: [$tst]\n";
	}
}
#====================================================================
sub lex_prob {
	my (%db) 	 = (%{shift(@_)});
	my $src 	 = shift(@_);
	my $tst 	 = shift(@_);
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
sub get_align_prob {
	my $f = shift(@_);
	my $lex_db = shift(@_);
	my (@ngram) = (@{shift(@_)});
	my $sent_prob = shift(@_);

	my (%prob, %dict) = ();
	foreach my $e ( @ngram ) {
		my $k = "$f:$e";
		my $score = 0;
		$lex_db->db_get($k, $score);

		if( defined($score) && $prob{$f} < $score ) {
			$dict{$f} = $k;
			$prob{$f} = $score;
		}
	}

	foreach my $f ( keys %prob ) {
		$sent_prob->{"cnt"}++;
		$sent_prob->{"sum"} += log($prob{$f});
		# print STDERR "# $f ($dict{$f}) := $prob{$f}\n" if( $_debug );
	}
}
#====================================================================
sub phrase_prob {
	my (%db) 		= (%{shift(@_)});
	my ($src_tag) 	= shift(@_);
	my ($trg_tag) 	= shift(@_);
	my (@sent) 		= (@{shift(@_)});
	my $features 	= shift(@_);

	# seek phrase-table
	my ($align) = ();
	my (%cnt) = ();
	my (%sum) = ();
	# my (%buf) = ();

	foreach my $s ( @sent ) {
		# printf STDERR Dumper($s) if( $_debug );

		my (%phrase) = (%{$s});

		$phrase{$src_tag} =~ s/^\s+|\s+$//g;
		$phrase{$trg_tag} =~ s/^\s+|\s+$//g;

		my $f = $phrase{$src_tag};
		my $e = $phrase{$trg_tag};
		my (%align) = get_align_info($phrase{"align"});

		$cnt{"count:unk"}++ if( $e =~ /\|UNK/i );
		$cnt{"count:phrase"}++;

		# printf STDERR "# f = $f, e = $e, align = %s\n", $phrase{"align"} if( $_debug );

		$e =~ s/\|UNK//g;

		my (@tok_f) = split(/\s+/, $f);
		my (@tok_e) = split(/\s+/, $e);

		$cnt{"token:f"} += scalar(@tok_f);
		$cnt{"token:e"} += scalar(@tok_e);

		# compute word align prob.
		foreach my $i ( sort keys %align ) {
			next if( $i eq "" );

			foreach my $j ( sort keys %{$align{$i}} ) {
				next if( $j eq "" );

				my $k = sprintf("%s:%s", $tok_f[$i], $tok_e[$j]);
				my $score = 0;
				$db{"lex"}->db_get($k, $score);

				$score = 0.00001 if( $score == 0 );

				# printf STDERR "# align: $i-$j = %f\t%s\t%s\n", $score, $tok_f[$i], $tok_e[$j] if( $_debug );

				$cnt{"prob:align"}++;
				$sum{"prob:align"} += $score;
			}
		}

		# compute phrase prob.
		if( defined($db{"phrase_table"}) ) {
			my $value = 0;
			$db{"phrase_table"}->db_get($f, $value);

			my ($score, $polymorphism) = get_phrase_prob($f, $value, $e);
			if( $score == 0 ) {
				$score = 0.00001;
				$polymorphism = 1;
			}

			# type 1
			$cnt{"prob:phrase"}++;
			$sum{"prob:phrase"} += $score;

			# push(@{$buf{"prob:phrase"}}, sprintf("p($f, $e, %f)", $score));

			# type 2
			# $cnt{"prob:phrase:polymorphism"}++;
			# $sum{"prob:phrase:polymorphism"} += $score + 1/$polymorphism;

			# push(@{$buf{"prob:phrase:polymorphism"}}, sprintf("p($f, $e, %f, %d)", $score, $polymorphism));
		} 

		# compute phrase lm score
		if( defined($db{"f_lm"}) ) {
			my $score = 0;
			$db{"f_lm"}->db_get($f, $score);

			# print STDERR "($f: $score)\n" if( $_debug );

			$score = -10  if( !defined($score) || $score eq "" );	

			# type 1
			$cnt{"plm:f"}++;
			$sum{"plm:f"} += $score;

			# push(@{$buf{"plm:f"}}, sprintf("p($f, %f)", $score));
		}

		if( defined($db{"e_lm"}) ) {
			my $score = 0;
			$db{"e_lm"}->db_get($e, $score);

			$score = -10  if( !defined($score) || $score eq "" );	

			# type 1
			$cnt{"plm:e"}++;
			$sum{"plm:e"} += $score;

			# push(@{$buf{"plm:e"}}, sprintf("p($f, %f)", $score));
		}
	}

	# summary
	foreach my $k ( qw/ count:phrase count:unk token:f token:e / ) {
		$cnt{$k} = 0 if( !defined($cnt{$k}) );

		$features->{$k} = $cnt{$k};
		# printf STDERR "($k:%d)\t", $cnt{$k} if( $_debug );
	}

	$features->{"diff:token"} = $features->{"token:f"} - $features->{"token:e"};

	foreach my $k ( qw/ prob:align plm:e plm:e prob:phrase / ) {
		$sum{$k} = 0.00001 if( !defined($sum{$k}) );
		
		# printf STDERR "($k:%f/%d)\n", $sum{$k}, $cnt{$k} if( $_debug );

		if( $k !~ /^plm/ ) {
			$sum{$k} = 0.00001 if( $sum{$k} == 0 );
			$sum{$k} = log($sum{$k});
		}

		$features->{$k} = 2**(-$sum{$k}/$cnt{$k});
	}

	$features->{"diff:plm"} = $features->{"plm:f"} - $features->{"plm:e"};

	# printf STDERR "\n" if( $_debug );
}
#====================================================================
sub get_pos_features {
	my $text = shift(@_);
	my $features = shift(@_);

	my (@token_pos) = split(/\s+/, $text);

	my (%pos_count) = ("V" => 0, "E" => 0, "N" => 0, "J" => 0, "X" => 0, "M" => 0);

	foreach my $p ( keys %pos_count ) {
		$features->{"pos:".$p} = 0;		
	}

	foreach my $word ( @token_pos ) {
		my ($w, $p) = split(/\//, $word, 2);
		$p =~ s/^(.).+$/$1/g;

		next if( !defined($pos_count{$p}) );
		$features->{"pos:".$p}++;
	}
}
#====================================================================
sub lm_score {
	my $lm_db 		= shift(@_);
	my $backoff_db 	= shift(@_);
	my $text 		= shift(@_);
	my $features 	= shift(@_);
	my $tag 		= shift(@_);

	my (@token) = split(/\s+/, $text);

	my (%ngram, %lm_score, %buf_log) = ();

	get_lm_candidate(\@token, 1, \@{$ngram{"1"}});
	($lm_score{"1"}) = get_lm_score($lm_db, $backoff_db, 1, \@{$ngram{"1"}});

	get_lm_candidate(\@token, 2, \@{$ngram{"2"}});
	($lm_score{"2"}) = get_lm_score($lm_db, $backoff_db, 2, \@{$ngram{"2"}});

	get_lm_candidate(\@token, 3, \@{$ngram{"3"}});
	($lm_score{"3"}) = get_lm_score($lm_db, $backoff_db, 3, \@{$ngram{"3"}});

	get_lm_candidate(\@token, 4, \@{$ngram{"4"}});
	($lm_score{"4"}) = get_lm_score($lm_db, $backoff_db, 4, \@{$ngram{"4"}});

	get_lm_candidate(\@token, 5, \@{$ngram{"5"}});
	($lm_score{"5"}) = get_lm_score($lm_db, $backoff_db, 5, \@{$ngram{"5"}});

	foreach my $k ( sort keys %lm_score ) {
		$features->{"lm:".$tag.":".$k} = 2**(-$lm_score{$k});
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

		my $score = 0;
		$lm_db->db_get($np, $score);

		if( defined($score) ) {
			$lm_score += $score;
			$ret{$np} += $score;
			next;
		} 

		# ignore smoothing
		if( $nosmoothing ) {
			$score = log(1/10000000000);

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

	# my (@buf) = ();
	# foreach my $k ( sort keys %ret ) { 
	# 	push(@buf, "p($k, $ret{$k})");
	# }

	my $cnt_ret = scalar(keys %ret);

	my $ret_score = $lm_score;
	$ret_score = $lm_score / $cnt_ret if( $cnt_ret > 0 );

	# if( $_debug ) {
	# 	print STDERR "\n# summary\n";

	# 	print STDERR "# p(".join(" | ", @lm_candidate).") ~= \n";
	# 	print STDERR "# ".join("\n# + ", @buf);
	# 	print STDERR "\n# ~= perplexity= ".(2**(-$ret_score)).", log(p)=$ret_score, ($lm_score / ".scalar(@buf).")";
	# 	print STDERR ", ".POSIX::pow(2, $lm_score)."\n\n";
	# }

	# return POSIX::pow(2, $lm_score);
	return ($ret_score);
}
#====================================================================
sub get_backoff
{	
	my $lm_db = shift(@_);
	my $backoff_db = shift(@_);
	my $np = shift(@_);

	# print STDERR "\n# get_backoff\n" if( $_debug );

	my $score_backoff = 0;
	# my (@backoff_log) = ();

	my $needle = $np;
	$needle =~ s/^[ ]+ //;

	# $ret{$needle} += 0;
	my $score = 0;
	$lm_db->db_get($needle, $score);

	if( defined($score) ) {
		$score_backoff += $score;
		# push(@backoff_log, "p($needle, $score)");

		# printf STDERR "# \t%s\n", join("+", @backoff_log) if( $_debug );

		return $score_backoff;
	}

	# p(a b c) = p(c) + b(b) + b(a b)
	# p(d | a b c) = p(d) + b(c) + b(b c) + b(a b c)
	# b( so | i love you) = p(so) + b(you) + b(love you) + b(i love you)

	return $score_backoff if( !defined($backoff_db) );

	my (@token_np) = split(/ /, $np);
	$needle = pop(@token_np);

	if( $needle ne "</s>" ) {
		$lm_db->db_get($needle, $score);

		if( defined($score) ) {
			$score_backoff += $score;
			# push(@backoff_log, "p($needle, $score)");
		# } else {
		# 	push(@backoff_log, "p($needle, null)");			
		}
	}

	for( my $i=0 ; $i<scalar(@token_np) ; $i++ ) {
		$needle = join(" ", @token_np[($#token_np-$i)..$#token_np]);

		next if( $needle eq "<s>" || $needle eq "</s>" );

		$backoff_db->db_get($needle, $score);
		if( !defined($score) ) {
			# push(@backoff_log, "b($needle, null)");			
			next;
		}

		$score_backoff += $score;			
		# push(@backoff_log, "b($needle, $score)");			
	}

	# printf STDERR "# \tp(%s) := %f, %s\n", $np, $score_backoff, join(" + ", @backoff_log) if( $_debug );

	# return $score_backoff/scalar(@backoff_log);
	return $score_backoff;
}
#====================================================================
sub get_lm_candidate
{
	my (@token) = (@{shift(@_)});
	my $n 		= shift(@_);
	my $ret 	= shift(@_);

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

	# if( $_debug ) {
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

	# if( $_debug ) {
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
sub get_phrase_prob 
{
	my $k = shift(@_);
	my $phrase_v = shift(@_);
	my $phrase = shift(@_);

	$phrase_v = decode('UTF-8', $phrase_v, Encode::FB_CROAK);

	my (@token) = split(/ \|\|\| /, $phrase_v);

	# printf STDERR "# $k => [$phrase] := [%s]\n", join(", ", @token) if( $_debug );

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

	# printf STDERR "# $k => [$sum]\n" if( $_debug );

	return ($probability, scalar(@token));
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
