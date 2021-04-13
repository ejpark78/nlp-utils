#!/usr/bin/perl -w

use strict;
use utf8;

# use lib "$ENV{TOOLS}";
# require "smi/smi.pm";

# use FindBin qw($Bin);
# use lib "$Bin";
# require "smi.pm";

use FindBin qw($Bin);
use lib "$Bin";

require "Sentence.pm";


sub open_smi_db {
	my $db_name = shift(@_);
	
	# to use if( defined($dbh->errstr) ): PrintError => 0, RaiseError => 0
	my $dbh = DBI->connect("DBI:SQLite:dbname=".$db_name, "", "",
						   {AutoCommit => 1, PrintError => 0, RaiseError => 0});

	# Maximise compatibility
	$dbh->do('PRAGMA legacy_file_format = 1');

	# Turn on all the go-faster pragmas
	$dbh->do('PRAGMA synchronous  = 0');
	$dbh->do('PRAGMA temp_store   = 2');
	$dbh->do('PRAGMA journal_mode = OFF');
	$dbh->do('PRAGMA locking_mode = EXCLUSIVE');
	
	return $dbh;
}


sub smi_to_text {
	my $smi = shift(@_);

	$smi = decode("utf-8", $smi);
	# print($smi);
	
	my (%data) = ();
	my ($sync_no, $start, $caption) = ("", "", "");

	foreach my $line ( split(/\n/, $smi) ) {
		$line =~ s/^\s+|\s+$//g;

		if( $line =~ m/<SYNC Start=(\d+)>/i ) {
			$start = $sync_no;
			$sync_no = $1;

			$caption =~ s/<.+?>//g;
			$caption =~ s/\{.+?\}//g;
			$caption =~ s/\s+/ /g;

			$caption =~ s/&nbsp;/ /g;
			$caption =~ s/&nbsp/ /g;

			$caption =~ s/ \/ / - /g;

			$caption =~ s/(,|\?|!|;|\")([^ 0-9])/$1 $2/g;

			$caption =~ s/(\?|\.|\!)\s+(\?|\.|\!)/$1$2/g;

			$caption =~ s/\?\!|\!\?/\?/g;

			$caption =~ s/(\"|\'|\!|\?)+/$1/g;

			$caption =~ s/(\.|\!|\?) ([a-z])/$1 \U$2/g;

			$caption =~ s/ i / I /g;
			$caption =~ s/^i /I /;
			
			$caption =~ s/ I-I-I / I /g;
			$caption =~ s/ I-I / I /g;
			$caption =~ s/ I I/ I/g;

			$caption =~ s/\s+/ /g;
			$caption =~ s/^\s+|\s+$//g;

			if( $caption ne "" && $start ne "" ) {
				$data{$start}{$sync_no} .= "\t" if( defined($data{$start}{$sync_no}) );
				$data{$start}{$sync_no} .= $caption." ";
			}

			$caption = $line;
			next;
		}

		$line .= "." if( $line =~ m/(요|상관없어|이군|겠지|니다|었소|였소|거죠|거야|꺼다|았어|있어|했소|겠다|겼다| 해)$/ );
		$caption .= $line." ";		
	}

	return to_list(\%data);
}


sub get_smi_text_to_list {
	my (@data)   = (@{shift(@_)});
	my $smi_text = shift(@_);
	my $text_ko  = shift(@_);
	my $text_en  = shift(@_);
	
	for( my $i=0 ; $i<scalar(@data) ; $i++ ) {
		my ($ko, $en) = ($data[$i]->{"ko"}, $data[$i]->{"en"});

		next if( $ko eq "" || $en eq "" );

		push(@{$smi_text}, sprintf("%d ~ %d\t%s\t%s",
			$data[$i]->{"start"}, $data[$i]->{"end"}, $en, $ko));

		push(@{$text_ko}, $ko);
		push(@{$text_en}, $en);
	}
}


sub to_list {
	my (%data) = (%{shift(@_)});

	my (@list) = ();
	foreach my $start ( sort {$a<=>$b} keys %data ) {
		next if( $start eq "" );

		foreach my $end ( sort {$a<=>$b} keys %{$data{$start}} ) {
			my ($ko, $en) = split_koen($data{$start}{$end});
	
			next if( $ko eq "" || $en eq "" );

			my (%item) = (
				"start" => $start, 
				"end" => $end, 
				"ko" => $ko, 
				"en" => $en, 
				"text" => $data{$start}{$end}
			);

			push(@list, \%item);
		}
	}	

	return (@list);
}


sub split_koen {
	my $line = shift(@_);

	my (@ko, @en) = ();
	foreach my $item ( split(/\t/, $line) ) {
		$item =~ s/^\s+|\s+$//g; 
		$item =~ s/\s+/ /g; 

		next if( $item eq "" );

		if( $item =~ /\p{Hangul}+/ ) {
			push(@ko, $item);
		} elsif( $item =~ /[a-z]/i ) {
			push(@en, $item);
		}
	}

	return (join(" ", @ko), join(" ", @en));
}


sub reform_puncuation {
	my $str = shift(@_);

	$str =~ s/(\?|\.|\!)\s+(\?|\.|\!)/$1$2/g;

	return $str;
}


sub reform_quote {
	my $str = shift(@_);

	$str =~ s/^\s+|\s+$//g;

	$str =~ s/^\"([^"]+)$/$1/g;
	$str =~ s/^\'([^']+)$/$1/g;

	$str =~ s/^([^"]+)\"\s*$/$1/g;
	$str =~ s/^([^']+)\'\s*$/$1/g;

	$str =~ s/^\"([^"]+)\"\s*$/$1/g;
	$str =~ s/^\'([^']+)\'\s*$/$1/g;

	$str =~ s/\"([^ ])/\" $1/g;

	$str =~ s/\"\s*([^"]+)\s*\"/\"$1\"/g;
	$str =~ s/\'\s*([^']+)\s*\'/\'$1\'/g;
	
	$str =~ s/^\s+|\s+$//g;

	return $str;
}


sub set_korean_punctuation {
	my $text = shift(@_);
	
	$text =~ s/(예요|네요|어요|대요|고요|상관없어|이군|겠지|니다|었소|였소|거죠|거야|꺼다|았어|있어|했소|겠다|겼다| 해)( |$)/$1. /g;
	
	return $text;
}


sub join_single_char {
	my $text = shift(@_);
	
	$text =~ s/^(.)\n/$1/sg;
	$text =~ s/\n(.)(\n|$)/$1$2/sg;
	$text =~ s/\n+/\n/sg;

	$text =~ s/^\s+|\s+$//g;
	
	return $text;
}


sub split_sentence {
	my $data = shift(@_);
	my (@data) = (@{$data});

	my $splitter = Sentence->new("en");

	my (@ret) = ();
	for( my $i=0 ; $i<scalar(@data) ; $i++ ) {
		my $ko = $data[$i]->{"ko"};
		my $en = $data[$i]->{"en"};

		# 516082 ~ 518016	Who's gonna find out? The American people?	누가 알겠나? 미국 국민이?
		# 1819717 ~ 1821275	It couldn't have been simpler. Kittens.	간단한 거잖아. 새끼 고양이!

		$ko = set_korean_punctuation($ko);
		
		$ko =~ s/(\?|\.|\!)\s+(\?|\.|\!)/$1$2/g;
		$en =~ s/(\?|\.|\!)\s+(\?|\.|\!)/$1$2/g;

		$ko =~ s/(\?|\.|\!)\s*(\p{Hangul})/$1\n$2/sg;
		$ko =~ s/(\?|\.|\!) ([^\?\.\!\"\'])/$1\n$2/sg;
		
		$en = $splitter->split($en);

		$ko = join_single_char($ko);
		$en = join_single_char($en);

		my (@token_ko) = split(/\n/, $ko);
		my (@token_en) = split(/\n/, $en);
		
		if( $ko eq "" || (scalar(@token_ko) > 1 && scalar(@token_ko) == scalar(@token_en)) ) {
			for( my $j=0 ; $j<scalar(@token_ko) ; $j++ ) {
				$token_ko[$j] =~ s/^\s+|\s+$//g;
				$token_en[$j] =~ s/^\s+|\s+$//g;
				
				next if( $token_ko[$j] eq "" && $token_en[$j] eq "" );
				next if( $token_ko[$j] =~ /\@|http/ || $token_en[$j] =~ /\@|http/ );

				my (%item) = (
					"fn" 	=> $data[$i]->{"fn"}, 
					"start" => $data[$i]->{"start"}, 
					"end" 	=> $data[$i]->{"end"}, 
					"ko" 	=> $data[$i]->{"ko"}, 
					"en" 	=> $data[$i]->{"en"}
				);

				$item{"ko"} = $token_ko[$j];
				$item{"en"} = $token_en[$j];
				
				$item{"ko"} = reform_quote($item{"ko"});
				$item{"en"} = reform_quote($item{"en"});
				
				if ( $item{"ko"} eq $item{"ko"} && $item{"ko"} =~ /^.$/ ) {
                    next
                }

				push(@ret, \%item);
			}
		} else {
			my (%item) = (
				"fn" 	=> $data[$i]->{"fn"}, 
				"start" => $data[$i]->{"start"}, 
				"end" 	=> $data[$i]->{"end"}, 
				"ko" 	=> $data[$i]->{"ko"}, 
				"en" 	=> $data[$i]->{"en"}
			);

			$item{"ko"} = reform_quote($item{"ko"});
			$item{"en"} = reform_quote($item{"en"});

			if( $item{"ko"} !~ /\@|http/ && $item{"en"} !~ /\@|http/ ) {
				push(@ret, \%item);
			}
		}
	}

	(@{$data}) = (@ret);
}


sub split_dash {
	my $data = shift(@_);
	my (@data) = (@{$data});
	my $opt_dash = shift(@_);

	my (@ret) = ();
	for( my $i=0 ; $i<scalar(@data) ; $i++ ) {
		my $ko = $data[$i]->{"ko"};
		my $en = $data[$i]->{"en"};

		$ko =~ s/^\s*-\s*//;
		$en =~ s/^\s*-\s*//;
		
		$ko =~ s/ -\s*/\n/g;
		$en =~ s/ -\s*/\n/g;
		
		$ko = join_single_char($ko);
		$en = join_single_char($en);		

		my (@token_ko) = split(/\n+/, $ko);
		my (@token_en) = split(/\n+/, $en);

		if( scalar(@token_ko) > 1 && scalar(@token_ko) == scalar(@token_en) ) {
			for( my $j=0 ; $j<scalar(@token_ko) ; $j++ ) {
				$token_ko[$j] =~ s/^\s+|\s+$//g;
				$token_en[$j] =~ s/^\s+|\s+$//g;

				next if( $token_ko[$j] eq "" && $token_en[$j] eq "" );

				my (%item) = (
					"fn" 	=> $data[$i]->{"fn"}, 
					"start" => $data[$i]->{"start"}, 
					"end" 	=> $data[$i]->{"end"}, 
					"ko" 	=> $data[$i]->{"ko"}, 
					"en" 	=> $data[$i]->{"en"}
				);

				if( defined($opt_dash) && $opt_dash eq "no dash" ) {
					$item{"ko"} = $token_ko[$j];
					$item{"en"} = $token_en[$j];
                } else {
					$item{"ko"} = "- ".$token_ko[$j];
					$item{"en"} = "- ".$token_en[$j];
				}
                
				push(@ret, \%item);
			}
		} else {
			my (%item) = (
				"fn" 	=> $data[$i]->{"fn"}, 
				"start" => $data[$i]->{"start"}, 
				"end" 	=> $data[$i]->{"end"}, 
				"ko" 	=> $data[$i]->{"ko"}, 
				"en" 	=> $data[$i]->{"en"}
			);

			if( defined($opt_dash) && $opt_dash eq "no dash" ) {
				$item{"ko"} =~ s/^\s*-\s*|\s+$//g;
				$item{"en"} =~ s/^\s*-\s*|\s+$//g;
			} 

			push(@ret, \%item);
		}
	}

	(@{$data}) = (@ret);
}


sub merge_empty {
	my $data = shift(@_);
	my (@data) = (@{$data});

	for( my $i=1 ; $i<scalar(@data)-1 ; $i++ ) {
 		next if( $data[$i]->{"ko"} ne "" && $data[$i]->{"en"} ne "" );

# 225514 ~ 227870	Wow. Behavioral Analysis Unit. You work with Gideon?	와우, '행동 분석단'이네요?
# 227870 ~ 229170		기디언 요원과 같이 일해요?

# 229496 ~ 231281	Were you with him in Boston?	보스턴에서 그 분과 같이 일했어요?

		my $overlap_prev = $data[$i]->{"start"}   - $data[$i-1]->{"end"};
		my $overlap_next = $data[$i+1]->{"start"} - $data[$i]->{"end"};

		# print "overlap_prev: $overlap_prev, $overlap_next\n$ko\n";

		if( $overlap_prev < 100 && $overlap_prev <= $overlap_next ) {			
			merge_item($data[$i-1], $data[$i]);
		}
	}

	my (@clean) = trim_list(\@data);
	(@{$data}) = (@clean);	
}


sub merge_sentence {
	my $data = shift(@_);
	my (@data) = (@{$data});

	for( my $i=1 ; $i<scalar(@data) ; $i++ ) {
		# 1578610 ~ 1579736	I guard	
		# 1581112 ~ 1582977	the American dream.	
		# 1585617 ~ 1586743	I guard	
		# 1587619 ~ 1590679	the American dream.
		
		# 1262408 ~ 1263793	Senor Esparza,	에스빠르사 씨
		# 1263793 ~ 1267982	we know that you have been using old parts	당신이 회사 비행기에
		# 1267982 ~ 1270699	on company planes...	중고품을 쓰고 있었다는 걸 압니다.
		# 1271295 ~ 1274332	and I wanted to know why	그 이유를 알고 싶군요.
		# 1275380 ~ 1277789	You making money on the side?	뒷돈을 벌고 있었던 거요?
		
		# 32490 ~ 35026	And I suppose that it's more than possible... 	 그가 비밀스런 사생활을 위해
		# 35026 ~ 37822	...he concocted this elaborate deception... 	 눈속임용으로
		# 38062 ~ 41461	...to have some privacy while he indulged in his secret life. 	 창녀를 찾는다는 건 충분히 간파 할 수 있을텐데요?

		my $en1 = $data[$i-1]->{"en"};
		my $en2 = $data[$i]->{"en"};
		
		$en1 =~ s/^\s+//g;
		$en2 =~ s/^\s+//g;
		
		$en2 =~ s/^\.{3,}+|\.{3,}+$//g;

		if( $en1 !~ /(\.|\?|\!)$/ && $en2 =~ /^[^A-Z]/ ) {
			merge_item($data[$i-1], $data[$i]);
		}
	}

	my (@clean) = trim_list(\@data);
	(@{$data}) = (@clean);	
}


sub merge_overlap {
	my $data = shift(@_);
	my (@data) = (@{$data});

	for( my $i=1 ; $i<scalar(@data) ; $i++ ) {
		if( $data[$i-1]->{"end"} > $data[$i]->{"start"} ) {
			merge_item($data[$i-1], $data[$i]);
		}
	}

	my (@clean) = trim_list(\@data);
	(@{$data}) = (@clean);
}


sub merge_item {
	my $a = shift(@_);
	my $b = shift(@_);

	$b->{"fn"} 	  = $a->{"fn"};
	$b->{"start"} = $a->{"start"};
	$b->{"ko"}    = $a->{"ko"}." ".$b->{"ko"};
	$b->{"en"}    = $a->{"en"}." ".$b->{"en"};

	$b->{"ko"} =~ s/\s+/ /g;
	$b->{"en"} =~ s/\s+/ /g;

	$b->{"ko"} =~ s/\.{3,}+([^A-Z])/ $1/g;
	$b->{"en"} =~ s/\.{3,}+([^A-Z])/ $1/g;

	$b->{"ko"} =~ s/^\s+|\s+$//g;
	$b->{"en"} =~ s/^\s+|\s+$//g;

	$a->{"fn"}    = "";
	$a->{"start"} = -1;
	$a->{"end"}   = -1;
	$a->{"ko"}  = "";
	$a->{"en"}  = "";
}


sub trim_list {
	my (@data) = (@{shift(@_)});

	my (@ret) = ();
	for( my $i=0 ; $i<scalar(@data) ; $i++ ) {
		next if( $data[$i]->{"start"} == -1 );

		push(@ret, $data[$i]);
	}

	return (@ret);
}


sub get_ngram
{
	my (@token) = (@{shift(@_)});
	my $n = shift(@_);
	my $ret = shift(@_);

	$n--;

	for( my $i=0 ; $i<scalar(@token)-$n ; $i++ ) {
		my $buf = join(" ", @token[$i..($i+$n)]);

		$buf =~ s/\s+$//;
		$buf =~ s/\s+/ /g;

		next if( $buf eq "" );

		push(@{$ret}, $buf);
	}
}


sub comma {
	my $cnt = shift(@_);

	$cnt = sprintf("%d", $cnt);
	for ( my $i = -3; $i > -1 * length($cnt); $i -= 4 ){
	    substr( $cnt, $i, 0 ) = ',';
	}

	return $cnt;
}


1

__END__
