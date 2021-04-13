#!/usr/bin/perl -w
#====================================================================
use strict;
#====================================================================
# SUB. FUNCTIONS
#====================================================================
# use lib "$ENV{TOOLS}/bin";
# require "align.pm";
#====================================================================
sub AlignWord {	
	my (%dict_roman) = ();
	ReadDictRoman($ENV{scripts}."/dict.kren.roman.utf8", \%dict_roman);
	
	print STDERR "# SCAN CORPUS ...\n";
	
	foreach my $line ( <STDIN> ) {	
		$line =~ s/^\s+|\s+$//g;
		
		if( $line eq "" ) {next}

		my ($kr, $en) = split(/\t/, $line, 2);
		
		if( !defined($kr) || !defined($en) ) {next}
		
		print "kr: $kr\n";
		print "en: $en\n";
		
		foreach my $feature ( GetFeatureList($kr) ) {
			print "# ".$feature."\n";
		}

		my (%ret) = GetRoman($kr, $en, \%dict_roman);
		foreach my $w1 ( keys %ret ) {
			foreach my $w2 ( keys %{$ret{$w1}} ) {
				print $w1."\t".$w2."\n";
			}
		}
	}
}
#====================================================================
sub GetRoman {
	my ($_kr, $_en, $dict, $_debug) = @_;

	my (%ret) = ();

	$_kr =~ s/\p{^Hangul}/ /g;
	$_en =~ s/\p{^Latin}/ /g;
	
	$_kr =~ s/\s+/ /g;
	$_en =~ s/\s+/ /g;

	print "\t GetRoman: ================================\n" if( defined($_debug) );

	foreach my $word ( split(/ /, $_kr ) ) {
		$word =~ s/(\p{Hangul})/$1 /g;
		my ($word1, $word2) = GetRomanAtWord($word, $_en, $dict, $_debug);
		
		next if( $word1 eq "" );
		
		$ret{$word1}{$word2} = 1;
	}

	return (%ret);
}	
#====================================================================
sub GetRomanAtWord {
	my ($_word, $_en, $_dict, $_debug) = @_;
	
	print "\n" if( defined($_debug) );

	# make pattern (roman)
	my $pattern = "";
	foreach my $slla ( split(/ /, $_word) ) {
		my $buf = "";
		foreach my $word ( keys %{$_dict->{$slla}} ) {
			$buf .= "|" if( $buf ne "" );
			$buf .= $word;
		}

		if( $buf ne "" ) {
			$pattern .= " " if( $pattern ne "" );
			$pattern .= "(".$buf.")";
		}
	}

	return ("", "") if( $pattern eq "" );

	print "\t_WORD: ".$_word."\n\t_EN: ".$_en."\n\tPATTERN: ".$pattern."\n" if( defined($_debug) );

	# compare
	my $max_cnt = 2;
	
	my (@token_t) = split(/ /, $pattern);
	for( my $i=$#token_t ; $i>=0 ; $i-- ) {
		my $needle = "";
		foreach( @token_t[0..$i] ) {$needle .= $_."[ ]*"}

		print "\t _en: ".$_en."\n" if( defined($_debug) );
		print "\t needle: ".$needle."\n" if( defined($_debug) );

		if( $_en =~ m/($needle) /i ) {
			my $word_t = $1;

			print "\tword_t: ".$word_t."\n" if( defined($_debug) );

			if( $word_t =~ m/^[a-z]/ ) {next}

			my (@token_s) = split(/ /, $_word);

			my $buf = "";
			foreach( @token_s[0..$i] ) {$buf .= $_}

			return ("","") if( length($word_t) < 2 || length($buf) < 2 );
			
			print "\t".$word_t."\t".$buf."\n\n" if( defined($_debug) );

			return ($buf, $word_t);
		}

		return ("", "") if( $max_cnt-- < 0 );
	}
	
	return ("", "");
}
#====================================================================
sub MakeBitextSentence {
	my ($_sent_list_kr, $_sent_list_en, $_dict_kren, $_dict_roman) = @_;
	
	# make english feature
	my (%feature_list) = MakeFeatureList($_sent_list_en);
	
	# make korean feature & make common feature freq.
	my (%feature_matrix) = GetFeatureMatrix($_sent_list_kr, \%feature_list, $_dict_kren, $_dict_roman);
	
	my (%similarity_matrix) = GetSimilarityMatrix(\%feature_matrix);
	
	# make alignment
	my (%alignment_list) = GetAlignmentList(\%similarity_matrix);	

	# print result
	print "## RESULT ################################################\n\n";

	for( my $i=0 ; $i<scalar(@{$_sent_list_kr}) ; $i++ ) {print "# [".$i."] ".$_sent_list_kr->[$i]."\n"} print "\n";
	for( my $i=0 ; $i<scalar(@{$_sent_list_en}) ; $i++ ) {print "# [".$i."] ".$_sent_list_en->[$i]."\n"} print "\n";

	print "## Alignment Result ######################################\n\n";

	# merge sentence

	my (%uniq_kr, %uniq_en) = ();
	
	foreach my $idx_kr ( keys %alignment_list ) {
		my ($idx_en) = ( keys %{$alignment_list{$idx_kr}} );
		
		$uniq_kr{$idx_kr} = $uniq_en{$idx_en} = $idx_en;
	}

#	for( my $idx_kr=0 ; $idx_kr<scalar(@{$_sent_list_kr}) ; $idx_kr++ ) {
#		for( my $idx_en=0 ; $idx_en<scalar(@{$_sent_list_en}) ; $idx_en++ ) {			
#			if( !defined($alignment_list{$idx_kr}{$idx_en}) && !defined($uniq_en{$idx_en}) && defined($uniq_kr{$idx_kr - 1}) ) {				
#				my ($prev_idx_kr, $prev_idx_en, $l) = ();				
#				
#				($prev_idx_kr, $prev_idx_en) = ($idx_kr - 1, $uniq_kr{$idx_kr - 1});
#				
#				# merge rule no. 1
#				if( $idx_en - $prev_idx_en > 1 ) {
#					$alignment_list{$idx_kr}{$idx_en} = 1;
#				}
#
#				$l = length($_sent_list_en->[$prev_idx_en]) + length($_sent_list_en->[$idx_en]);
#				$l = ($l - length($_sent_list_kr->[$prev_idx_kr]));
##				$l = ($l - length($_sent_list_kr->[$prev_idx_kr])) / ($l + length($_sent_list_kr->[$prev_idx_kr]));
#				
##				$l = log($l);
#				
#				print sprintf("# ? [ %d - %d : %.2f : %.2f ] ", $prev_idx_kr, $idx_en, $similarity_matrix{$prev_idx_kr}{$idx_en}, $l);
#				print sprintf("[ %s ]\n", join(" | ", sort keys %{$feature_matrix{$prev_idx_kr}{$idx_en}})); 
#				
#				($prev_idx_kr, $prev_idx_en) = ($idx_kr, $uniq_kr{$idx_kr});
#
#				$l = length($_sent_list_en->[$prev_idx_en]) + length($_sent_list_en->[$idx_en]);
#				$l = ($l - length($_sent_list_kr->[$prev_idx_kr]));
##				$l = ($l - length($_sent_list_kr->[$prev_idx_kr])) / ($l + length($_sent_list_kr->[$prev_idx_kr]));
#				
##				$l = log($l);
#
#				print sprintf("# ? [ %d - %d : %.2f : %.2f ] ", $prev_idx_kr, $idx_en, $similarity_matrix{$prev_idx_kr}{$idx_en}, $l);
#				print sprintf("[ %s ]\n", join(" | ", sort keys %{$feature_matrix{$prev_idx_kr}{$idx_en}})); 
#
#				$uniq_en{$idx_en} = $idx_kr;
#			}
#			
#			if( !defined($alignment_list{$idx_kr}{$idx_en}) ) {next}
#			
#			my $l = length($_sent_list_en->[$idx_en]) - length($_sent_list_kr->[$idx_kr]);
#
#			print sprintf("# %d - %d # %.2f | %.2f # ", $idx_kr, $idx_en, $similarity_matrix{$idx_kr}{$idx_en}, $l);
#			print sprintf("[ %s ]", join(" | ", sort keys %{$feature_matrix{$idx_kr}{$idx_en}})); 
#			print "\n";
#			
#			last;
#		}
#	}
	
	print "\n\n\n";
	
	# print alignment result
	foreach my $idx_kr ( sort {$a<=>$b} keys %alignment_list ) {
		foreach my $idx_en ( sort {$a<=>$b} keys %{$alignment_list{$idx_kr}} ) {
			print sprintf("# %d - %d # %.2f # ", $idx_kr, $idx_en, $similarity_matrix{$idx_kr}{$idx_en});
			print sprintf("[ %s ]", join(" | ", sort keys %{$feature_matrix{$idx_kr}{$idx_en}})); 
			print "\n";
		}
	}
	
	print "\n\n\n";
}
#====================================================================
sub GetAlignmentList
{
	my ($_similarity_matrix) = @_;
	
	my (%rev_similiarity_matrix) = ();
	foreach my $idx_kr ( keys %{$_similarity_matrix} ) {
		foreach my $idx_en ( keys %{$_similarity_matrix->{$idx_kr}} ) {
			$rev_similiarity_matrix{$_similarity_matrix->{$idx_kr}{$idx_en}}{$idx_kr}{$idx_en} = 1;
		}
	}

	my (%alignment_list, %uniq_kr, %uniq_en) = ();	
	foreach my $similarity ( sort {$b<=>$a} keys %rev_similiarity_matrix ) {
		foreach my $idx_kr ( sort {$a<=>$b} keys %{$rev_similiarity_matrix{$similarity}} ) {
			if( defined($uniq_kr{$idx_kr}) ) {next}
			
			foreach my $idx_en ( sort {$a<=>$b} keys %{$rev_similiarity_matrix{$similarity}{$idx_kr}} ) {
				if( defined($uniq_en{$idx_en}) ) {next}
			
				$alignment_list{$idx_kr}{$idx_en} = $similarity;	
							
				$uniq_kr{$idx_kr} = $uniq_en{$idx_en} = 1;				
				last;
			}
		}
	}	

	return (%alignment_list);
}
#====================================================================
sub GetSimilarityMatrix
{
	my ($_feature_matrix) = @_;
	
	# make document freq.
	my (%document_freq) = ();
	foreach my $idx_kr ( keys %{$_feature_matrix} ) {		
		foreach my $idx_en ( keys %{$_feature_matrix->{$idx_kr}} ) {
			foreach my $word ( keys %{$_feature_matrix->{$idx_kr}{$idx_en}} ) {
				$document_freq{$word} += $_feature_matrix->{$idx_kr}{$idx_en}{$word};
			}
		}
	}

	# make similarity matrix
	my (%similarity_matrix) = ();
	foreach my $idx_kr ( keys %{$_feature_matrix} ) {		
		foreach my $idx_en ( keys %{$_feature_matrix->{$idx_kr}} ) {
			foreach my $word ( keys %{$_feature_matrix->{$idx_kr}{$idx_en}} ) {
				$similarity_matrix{$idx_kr}{$idx_en} += 1 / $document_freq{$word};
			}
		}
	}

	return (%similarity_matrix);
}
#====================================================================
sub GetFeatureMatrix
{
	my ($_sent_list, $_feature_list, $_dict_kren, $_dict_roman) = @_;
	
	my (%feature_matrix) = ();

	for( my $i=0 ; $i<=$#{$_sent_list} ; $i++ ) {
		my $line = $_sent_list->[$i];

		# scan number
		foreach my $feature ( GetFeatureList($line) ) {
			if( !defined($_feature_list->{$feature}) ) {next}
			
			foreach my $idx ( keys %{$_feature_list->{$feature}} ) {
				$feature_matrix{$i}{$idx}{$feature} += 0.05;
			}
		}

		# find roman feature
		foreach my $feature ( ToRoman($line, $_dict_roman) ) {
			if( !defined($_feature_list->{$feature}) ) {next}
			
			foreach my $idx ( keys %{$_feature_list->{$feature}} ) {
				if( $feature =~ /^(a|The|the|It|it|In|in)$/ ) {next}
				$feature_matrix{$i}{$idx}{$feature} += 1 / length($feature);
			}
		}
		
		# filter dict		
		foreach my $ngram ( GetFeatureNGram($line) ) {
			if( !defined($_dict_kren->{$ngram}) ) {next}
			
			foreach my $word ( keys %{$_dict_kren->{$ngram}} ) {
				if( !defined($_feature_list->{$word}) ) {next}
				
				foreach my $idx ( keys %{$_feature_list->{$word}} ) {
					if( $word =~ /[0-9A-Z]/ ) {
						$feature_matrix{$i}{$idx}{$word} += 0.25;
					} else {
						$feature_matrix{$i}{$idx}{$word} += 1;
					}
				}
			}
		}
	}

	return (%feature_matrix);
}
#====================================================================
sub MakeFeatureList
{
	my ($_sent_list) = @_;
	
	my (%feature_list) = ();	
	for( my $i=0 ; $i<=$#{$_sent_list} ; $i++ ) {
		my $line = $_sent_list->[$i];
		
		# scan number
		foreach my $feature ( GetFeatureList($line) ) {$feature_list{$feature}{$i} += 1}

		# token sentence
		$line =~ s/(, |\"|\'|\(|\)|\[|\]|\{|\}|\?|\<|\>|\!|\-)|\.$/ /g;

		foreach my $word ( split(/\s+/, $line) ) {
			$feature_list{$word}{$i} += 0.75;
			
			$word = lc($word);
			$feature_list{$word}{$i} += 1 if( !defined($feature_list{$word}{$i}) );
			
			if( $word =~ s/ves$/f/  && !defined($feature_list{$word}{$i}) ) {$feature_list{$word}{$i} += 1}
			if( $word =~ s/ies$/y/  && !defined($feature_list{$word}{$i}) ) {$feature_list{$word}{$i} += 1}
			if( $word =~ s/(e)*s$// && !defined($feature_list{$word}{$i}) ) {$feature_list{$word}{$i} += 1}
		}
	}
	
	return (%feature_list);
}
#====================================================================
sub ToRoman
{
	my ($_str, $_dict) = @_;

	$_str =~ s/\p{^Hangul}/ /g;
	$_str =~ s/(.)/$1 /g;

	my (%buf) = ();
	foreach my $key ( split(/\s+/, $_str) ) {
		next if( !defined($_dict->{$key}) );
		
		foreach my $val ( keys %{$_dict->{$key}} ) {$buf{$val} = 1}
	}
	
	return (keys %buf);
}
#====================================================================
sub GetFeatureList
{
	my ($_str) = @_;
	
	$_str =~ s/^\s+|\s+$//g;
	$_str =~ s/\s+/ /g;
	$_str =~ s/(, |\"|\'|\(|\)|\[|\]|\{|\}|\?|\<|\>|\!|\-)|\.$/ /g;
	
	$_str = " ".$_str." ";
	
	use utf8;

	my (@pattern) = (
					"([0-9]+(조|억|만|천|백|십|년|명|여명|여원))+", 
					"[0-9]+([.,][0-9]+)*\\s*(%|m|t|km|mm|톤|미터|킬로)", 
					"[0-9]+(월|일)", 
					" [월화수목금토일]요일 ", 
					" [0-9]+([.,][0-9]+)*", 
					" [A-Z][a-z]+ ", 
					" ([A-Z]+\\.*)+ ", 
					" [A-Z]+ ", 
					"[0-9]+", 
	);
	
	my (%number_list) = ();
	
	my $max_cnt = 100;
	
	for( my $i=0 ; $i<=$#pattern ; ) {
		my $needle = $pattern[$i];
		
		$_str =~ s/($needle)/ /;
		
		if( $max_cnt-- < 0 ) {
			$max_cnt = 100;
			$i++;
			next;
		}
			
		if( defined($1) && $1 ne "(" && $1 ne ")" ) {
			my $text = $1;
			
			$text =~ s/^\s+|\s+$//g;

			$number_list{$text} = 1;

			if( $text =~ /(\d*)(조|억|만|천|백|십)(\d*)/ ) {			
				my ($num1, $unit, $num2) = ($1, $2, $3);
				
				my $num = 0;
				if( defined($unit) ) {
					if( !defined($num1) ) {$num1 = 1} 
	
					$num += $num1 * 100000000 	if( $unit eq "억" );
					$num += $num1 * 10000 	 	if( $unit eq "만" );
					$num += $num1 * 1000		if( $unit eq "천" );
					$num += $num1 * 100			if( $unit eq "백" );
					$num += $num1 * 10			if( $unit eq "십" );
				}
				
				if( defined($num2) && $num2 =~ /^\d+$/ ) {$num += $num2}
				
				if( $num != 0 ) {$number_list{$num} = 1}
			} 
			
			if( $text =~ /(\d+)년/ ) {							
				my $year = $1;
				
				$number_list{$year} = 1;				
				if( length($year) == 2 ) {$number_list{"19".$year} = 1}
			}

			if( $text =~ /([0-9]+([.,][0-9]+)*\s*)(%|m|t|km|mm|톤|미터|킬로|명|여명|여원|일)/ ) {							
				my $num = $1;
				
				$num =~ s/^\s+|\s+$//g;
				$number_list{$num} = 1;
			}
			
			if( $text =~ /^[0-9]+([,][0-9])*$/ ) {
				$text =~ s/,//g;
				
				$number_list{$text} = 1;
			}
			
			next;
		}
		
		$i++;
	}

	return (keys %number_list);
}
#====================================================================
sub GetFeatureNGram
{
	my ($_str) = @_;
	
	$_str =~ s/^\s+|\s+$//g;
	$_str =~ s/\s+/ /g;
	
	my (%token_list) = ();
	foreach my $word ( split(/ /, $_str) ) {
		$word =~ s/(.)/$1 /g;

		my (@token) = split(/ /, $word);
		for( my $i=0 ; $i<=$#token ; $i++ ) {
			for( my $j=$i ; $j<=$#token ; $j++ ) {
				my $buf = join("", @token[$i..$j]);
				
				$token_list{$buf} = 1;
			}
		}
	}
	
	return (keys %token_list);
}
#====================================================================
sub ReadDict
{
	use PerlIO::gzip;

	my ($_fn, $_dict, $_progress) = @_;

	print STDERR "# Loading Dict ".$_fn."...\n";

	my $open_mode = "<";
	$open_mode = "<:gzip" if( $_fn =~ /\.gz$/ );

	die "can not open ".$_fn.": ".$!."\n" unless( open(FILE_DICT, $open_mode, $_fn) );
	
	binmode(FILE_DICT, ":utf8");

	my $cnt = 0;
	foreach my $line ( <FILE_DICT> ) {
		$line =~ s/^\s+|\s+$//g;

		my ($kr, $en) = split(/\t/, $line, 2);

		next if( !defined($kr) || !defined($en) );
		
		$kr =~ s/^\s+|\s+$//g;
		$en =~ s/^\s+|\s+$//g;

		next if( defined($_dict->{$kr}{$en}) );

		$_dict->{$kr}{$en} = 1;
		$_dict->{$kr}{lc($en)} = 0.5 if( !defined($_dict->{$kr}{lc($en)}) );

		print STDERR "\r($cnt)" if( $_progress && ($cnt++ % 10000) == 0 );
	}

	print STDERR "\n# Dict Entity: ".GetCount($cnt)." ea\n\n" if( $_progress );

	close(FILE_DICT);
}
#===============================================================================
sub ReadDictRoman
{
	use PerlIO::gzip;

	my ($_fn, $_dict, $_progress) = @_;

	print STDERR "# Loading Dict ".$_fn."...\n";

	my $open_mode = "<";
	$open_mode = "<:gzip" if( $_fn =~ /\.gz$/ );

	die "can not open ".$_fn.": ".$!."\n" unless( open(FILE_DICT, $open_mode, $_fn) );
	binmode(FILE_DICT, ":utf8");

	my $cnt = 0;
	foreach my $line ( <FILE_DICT> ) {
		$line =~ s/^\s+|\s+$//g;

		my ($kr, $type, @val_list) = split(/\t/, $line);

		next if( !defined($kr) || scalar(@val_list) == 0 );
		
		$kr =~ s/^\s+|\s+$//g;

		foreach my $en ( @val_list ) {
			$en =~ s/^\s+|\s+$//g;

			if( $en eq "" ) {next}

#			print "'$kr' -> '$en'\n";

			$_dict->{$kr}{$en} = 1;

#			if( !defined($_dict->{$kr}{lc($en)}) ) {$_dict->{$kr}{lc($en)} = 0.5}
		}		

		if( $_progress && ($cnt++ % 10000) == 0 ) {print STDERR "#"}
	}

	if( $_progress ) {print STDERR "\n# Dict Entity: ".GetCount($cnt)." ea\n\n"}

	close(FILE_DICT);
}
#===============================================================================
sub GetCount {
	my ($_cnt) = @_;

	$_cnt =~ s/(\d)(?=(\d{3})+(\D|$))/$1\,/g;
	return $_cnt;
}
#====================================================================
sub TokenSentenceKorean {
	my ($_sentence) = @_;
	
	my (@sentence) = ();
	return (@sentence) if( $_sentence =~ /^\s*$/ );

	use utf8;
	
	$_sentence =~ s/^\s+|\s+$//g;	
	$_sentence =~ s/\s+/ /g;	
	$_sentence =~ s/([다라것])\.\s*/$1\.\n/g;

	foreach my $line ( split(/\n+/, $_sentence) ) {
		$line =~ s/^\s+|\s+$//g;
		next if( $line eq "" || $line eq "[EMPTY]" );
		
		push(@sentence, $line);
	}

	return (@sentence);
}
#====================================================================
sub TokenSentenceEnglish {
	my ($_sentence, $_abbr1, $_abbr2, $_abbr3) = @_;
	
	my (@sentence) = ();
	return (@sentence) if( $_sentence =~ /^\s*$/ );

	$_sentence =~ s/^\s+|\s+$//g;
	$_sentence =~ s/\s+/ /g;	
	
	no warnings;
	$_sentence =~ s/([^A-Z][!|?|.])(\"|\'|`|”|“|‘|’|[\xa1][\xb0\xb1\xae\xaf])*\s+(\"|\'|`|”|“|‘|’|[\xa1][\xb0\xb1\xae\xaf])*([A-Z])/$1$2\n$3$4/xg;
	
	use warnings;
	
	$_sentence =~ s/(\"|\'|`|”|“|‘|’|[\xa1][\xb0\xb1\xae\xaf])+\s+(\"|\'|`|”|“|‘|’[\xa1][\xb0\xb1\xae\xaf])+/$1\n$2/xg;
	
	$_sentence =~ s#($_abbr1)\.\n#$1\. #g;						# Delete new line at $abbr1
	$_sentence =~ s#($_abbr2)\. ([A-Z\"])#$1\.\n$2#g;			# New line at $abbr2
	$_sentence =~ s#($_abbr3)\.\n#$1\. #g;						# Delete new line at $abbr1
	$_sentence =~ s#^(\d+)\.\n#$1\. #g;	
	
	$_sentence =~ s#(\")([^\"]+)\n([^\"]+)(\")#$1$2$3$4#g;
	$_sentence =~ s#(\")([^\"]+)\n([^\"]+)\n([^\"]+)(\")#$1$2$3$4$5#g;
	
	foreach my $line ( split(/\n+/, $_sentence) ) {
		$line =~ s/^\s+|\s+$//g;
		next if( $line eq "" || $line eq "[EMPTY]" );
		
		push(@sentence, $line);
	}

	return (@sentence);
}
#====================================================================
sub LoadDictionaryAcronym {
	my ($acronym_file) = @_;

	open(ACRONYM, "<".$acronym_file) || die "can't open $acronym_file";
	my @acronym = <ACRONYM>;
	close ACRONYM;
	
	chomp(@acronym);

	my %acronym = ();
	foreach (@acronym) {
		s/\.//g;
		$acronym{$_}++;
	}

	@acronym = ();
	foreach (keys %acronym) {
		chop ;
		next if /^\s*$/;
		s#\.#\\\.#g;
		push(@acronym, $_);
	}
	return join("|", @acronym);
}
#====================================================================

1


__END__


feature list


서울시가 월요일 발표한 지난해 주민등록 인구통계에 따르면 중국인 거주자는 1만7432명으로 다른 국가에 비해 인구수가 가장 많았다는 것.
There were more Chinese residents in Seoul last year than any other foreign nationality, according to statistics compiled by the Seoul city government based on resident registration figures from 2000.


에 따르면 => according to





1만7432명 => 17,432 

1037만3234명 => 10,373,234


8.3% => 8.3% 

99년 => 1999

첫째 => First 

둘째 => Secondly 

셋째 => Thirdly

넷째 => Fourthly

김철환 => Kim Chul-Hwan


7월 => July

북한 => North Korea


