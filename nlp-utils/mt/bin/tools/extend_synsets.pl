#!/usr/bin/perl -w
#====================================================================
use strict;
use utf8;
use Encode;
use Getopt::Long;
use Tie::LevelDB; # google ngram
#====================================================================
my (%args) = (
	'ngram' => 3,
	'threshold' => 0
);

GetOptions(
	'eval_form' => \$args{"eval_form"},
	'src=s' => \$args{"src"},
	'ngram=s' => \$args{"ngram"},
	'threshold=s' => \$args{"threshold"},
	'dict=s' => \$args{"dict"}
);
#====================================================================
binmode(STDIN, ":utf8");
binmode(STDOUT, ":utf8");
binmode(STDERR, ":utf8");
#====================================================================
main: {
	my (@src) = read_src($args{"src"});
	my (%dict) = read_synsets($args{"dict"});

	my (%freq) = (
		"c" => 0,
		"cnt" => 0,
		"line_num" => 0,
		"ngram_sum" => 0,
		"ngram_cnt" => 0,
		"cnt_extend" => 0,
		"cnt_extend_line" => 0
	);

	my (%ngram_db) = ();

	# $ngram_db{"2"} = new Tie::LevelDB::DB("/home/ejpark/vols/vol1/books_google_ngrams_eng/2gms.leveldb");
	$ngram_db{"3"} = new Tie::LevelDB::DB("/home/ejpark/vols/vol1/books_google_ngrams_eng/3gms.leveldb");
	# $ngram_db{"4"} = new Tie::LevelDB::DB("/home/ejpark/vols/vol1/books_google_ngrams_eng/3gms.leveldb");
	# $ngram_db{"5"} = new Tie::LevelDB::DB("/home/ejpark/vols/vol1/books_google_ngrams_eng/3gms.leveldb");
	
	while( my $line = <STDIN> ) {
		$line =~ s/\s+$//;
		
		my (@token) = split(/ /, $line);

		my $qoute = 0;

		my (@sents, %idx_dict) = ();
		for( my $i=0 ; $i<scalar(@token) ; $i++ ) {
			my $w = $token[$i];

			$qoute ^= 1 if( $w =~ /(\"|\')/ );
			if( $qoute == 0 && $w =~ /^[a-z]/ ) {
				# my $e = lc $w;
				my $e = $w;
					
				push(@sents, $w);	
				if( defined($dict{$e}) ) {
					$freq{"c"}++;	
					(@{$idx_dict{$i}}) = (@{$dict{$e}});
				}
				$freq{"cnt"}++;
			} else {
				push(@sents, $w);	
			}
		}

		print STDERR "# ".join(" ", @sents)."\n\n";

		my (@result) = ($line);
		foreach my $pos ( keys %idx_dict ) {
			print STDERR "# $pos: ".$sents[$pos]." >".join(",", @{$idx_dict{$pos}})."\n";
			my (@extended_sents) = extend_sents(\@sents, \@{$idx_dict{$pos}}, $pos, \%ngram_db, \%args, \%freq);

			$freq{"cnt_extend"} += scalar(@extended_sents);
			foreach my $trg ( @extended_sents ) {
				push(@result, $trg);
			}
		}

		$freq{"cnt_extend_line"}++ if( scalar(@result) > 1 );

		if( !defined($args{"eval_form"}) ) {
			foreach my $ref ( @result ) {
				print $src[$freq{"line_num"}]."\t".$ref."\n";
			}
		} else {
			print $src[$freq{"line_num"}]."\t".join("\t", @result)."\n";
		}

		$freq{"line_num"}++;
	}

	$freq{"cnt_extend"}	+= $freq{"line_num"};

	print STDERR "# extended line count: \t".$freq{"cnt_extend_line"}."\n";
	print STDERR "# input sent count: \t".$freq{"line_num"}."\n";
	print STDERR "# output sent count: \t".$freq{"cnt_extend"}."\n";
	print STDERR "# dict. count: \t".$freq{"c"}."\n";
	print STDERR "# word count: \t".$freq{"cnt"}."\n";
	print STDERR "# ngram cnt: \t".$freq{"ngram_cnt"}."\n";
	print STDERR "# ngram sum: \t".$freq{"ngram_sum"}."\n";
}
#====================================================================
sub read_src
{
	my ($fn) = shift(@_);

	unless( open(SRC, "<", $fn) ) {die "can not open : ".$!."\n"}
	binmode(SRC, ":utf8");
	
	my (@ret) = (<SRC>);
	chomp(@ret);

	close(SRC);

	return (@ret);
}
#====================================================================
sub read_synsets
{
	my ($fn) = shift(@_);

	my (%dict) = ();

	unless( open(DICT, "<", $fn) ) {die "can not open : ".$!."\n"}
	binmode(DICT, ":utf8");
	
	foreach my $line ( <DICT> ) {
		$line =~ s/\s+$//;		

		my (@t) = split(/\t/, $line);

		# heart	bosom	intuition
		# heart	plane_figure
		# heart	playing_card
		# heart	pump	ticker	internal_organ

		# dict{"heart"} = @("bosom", "intuition");
		# dict{"bosom"} = @("heart", "intuition");
		# dict{"intuition"} = @("heart", "bosom");
		next if( $t[0] =~ /_/ );

		for( my $i=1 ; $i<scalar(@t) ; $i++ ) {
			next if( $t[$i] =~ /_/ );
			push(@{$dict{$t[0]}}, $t[$i]);		
		}
	}	
	close(DICT);

	return (%dict);
}
#====================================================================
sub extend_sents
{
	my (@sents) = @{shift(@_)};
	my (@dict) 	= @{shift(@_)};
	my $pos 	= shift(@_);
	my $ngram_db= shift(@_);
	my (%args) 	= %{shift(@_)};
	my $freq 	= shift(@_);

	my (@n) = (keys(%{$ngram_db}));

	my (@ret) = ();
	foreach my $v ( @dict ) {
		my (@buf) = ();
		for( my $i=0 ; $i<scalar(@sents) ; $i++ ) {
			my $w = ( $i == $pos ) ? $v : $sents[$i];
			push(@buf, $w);
		}

		# get ngram
		my (%ngram) = get_ngram(\@buf, $pos, \@n);

		# scoring
		my ($sum, $cnt, $ngram_cnt) = get_ngram_score(\%ngram, $ngram_db);

		$freq->{"ngram_sum"} += $sum;
		$freq->{"ngram_cnt"}++;

		if( $cnt > 0 && $sum > $args{"threshold"} ) {
			push(@ret, join(" ", @buf));
		}
	}

	return (@ret);
}
#====================================================================
sub get_ngram_score
{
	my (%ngram) = %{shift(@_)};
	my (%ngram_db) = %{shift(@_)};

	my $sum = 0;
	my $cnt = 0;
	my $total = 0;

	foreach my $n ( keys %ngram_db ) {
		foreach my $w ( @{$ngram{$n}} ) {
			my $v = $ngram_db{$n}->Get($w);
			$v = ( !defined($v) )? 0 : $v;
			$sum += $v;

			$total++;
			$cnt++ if( $v > 0 );

			# print STDERR "$n: $w:$v\n";
		}
	}

	return ($sum, $cnt, $total);
}
#====================================================================
sub get_ngram
{
	my (@sents) = @{shift(@_)};
	my $pos 	= shift(@_);
	my (@n) = @{shift(@_)};

	my (%ngram) = ();

	#  1,000 feet of aura below him 
	foreach my $n ( @n ) {
		$n--;

		my $start_pos = $pos - $n;
		my $end_pos = $pos + $n;

		for( my $i = $start_pos ; $i<$end_pos ; $i++ ) {
			my $length = $i+$n;

			next if( $i < 0 );
			last if( $i > $pos );
			last if( $length >= scalar(@sents) );

			push(@{$ngram{$n+1}}, join(" ", @sents[$i..$length]));
		}
	}

	return (%ngram);
}
#====================================================================
__END__      


cat full_set.data/data.en-ko.clean.en.tok \
| perl ~/tools/bin/extend_synsets.pl -dict ../wordnet3.0/noun.synsets


cat full_set.data/data.en-ko.clean.en.tok \
| perl ~/tools/bin/extend_synsets.pl \
-dict ../wordnet3.0/noun.synsets \
-src full_set.data/data.en-ko.clean.ko.tok \
> extended.ko-en

###############################

cat full_set.model/model.0/data/test.en-ko.en \
| perl ~/tools/bin/extend_synsets.pl \
-eval_form \
-dict ../wordnet3.0/noun.synsets \
-src full_set.model/model.0/data/test.en-ko.ko \
> extended.test.ko-en

cut -f1 extended.test.ko-en > extended.test.ko
cut -f2- extended.test.ko-en > extended.test.en

# sentence blue
perl ~/tools/bin/prepare_sent_bleu.pl \
  -src extended.test.ko \
  -tst $data_path/$test_set.$src-$trg.out$tag \
  -ref $data_path/$test_set.$src-$trg.$trg \
  | perl $tools/sent_bleu.pl \
  > $data_path/$test_set.$src-$trg$tag.sent_bleu

sync
