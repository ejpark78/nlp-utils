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
);

GetOptions(
	"debug" => \$args{"debug"},
	"max_bleu" => \$args{"max_bleu"},
	"sequence=s" => \$args{"sequence"}
);
#====================================================================
# MAIN
#====================================================================
main: {
	get_hybrid_score_best_tst(\%args);	
}
#====================================================================
# sub functions
#====================================================================
sub get_hybrid_score_best_tst {
	binmode(STDIN, ":utf8");
	binmode(STDOUT, ":utf8");
	binmode(STDERR, ":utf8");

	my (%param) = (%{shift(@_)});

	my (%sequence) = parse_sequence($param{"sequence"});

	# A	0.0000	0.43	0.0000	0.43	0.0000	[LM1,LM2,LM3,INPUT]	0.43	0.21	0.21	10 퍼센트 만 깎/V 아 주/V 시 면 사/V 겠 습니다 .	你 能 打九折 吗 就 买 。 	如果 你 给我 打 九 折 我 就 买它 。	如果 你 给我 打 九折 ， 我 就 买它 。	我 会 接受 的 如果 你 把 百分之十 折扣 给 我 。	0.0000	[LM1,LM2,LM3,INPUT]	0.43	0.21	0.21	10 퍼센트 만 깎/V 아 주/V 시 면 사/V 겠 습니다 .	减免 10% 的话 ， 买 。	如果 你 给我 打 九 折 我 就 买它 。	如果 你 给我 打 九折 ， 我 就 买它 。	我 会 接受 的 如果 你 把 百分之十 折扣 给 我 。
	while( my $line = <STDIN> ) {
		$line =~ s/\s+$//;

		next if( $line eq "" );
		next if( $line =~ /^#/ );

		my (@t) = split(/\t/, $line);

		my (%data) = ();
		$data{"tag"} = $t[$sequence{"tag"}];

		$data{"src"} = $t[$sequence{"src"}];
		if( $sequence{"ref"} =~ /,/ ) {
			$data{"ref"} = join("\t", @t[split(",", $sequence{"ref"})]);
		} else {
			$data{"ref"} = $t[$sequence{"ref"}];
		}

		if( $param{"max_bleu"} ) {
			if( $t[$sequence{"bleu_a"}] >= $t[$sequence{"bleu_b"}] ) {
				$data{"tst"} = $t[$sequence{"tst_a"}];
			} else {
				$data{"tst"} = $t[$sequence{"tst_b"}];				
			}
		} else {
			if( $data{"tag"} eq "A" ) {
				$data{"tst"} = $t[$sequence{"tst_a"}];
			} else {
				$data{"tst"} = $t[$sequence{"tst_b"}];
			}
		}

		# print $data{"tag"}."\n";
		printf "%s\t%s\t%s\n", $data{"src"}, $data{"tst"}, $data{"ref"};
	}
}
#====================================================================
sub parse_sequence {
	my $sequence = shift(@_);

	my $idx = 0;
	my (%input_sequence) = ();
	foreach my $pos ( split(/,/, $sequence) ) {
		$input_sequence{$pos} .= "," if( defined($input_sequence{$pos}) );
		$input_sequence{$pos} .= $idx;
		$idx++;
	}

	return (%input_sequence);
}
#====================================================================
#====================================================================
__END__

cut -f2,3,5 smt-genie.n3.ngram.txt.a > a
cut -f2,3,5 smt-genie.n3.ngram.txt.b > b

merge_file.pl a b | ../get_hybrid_score.pl -th 0.74 > best.smt-genie.n3.ngram.txt

