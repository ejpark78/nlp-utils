#!/usr/bin/perl -w
#====================================================================
use strict;
use utf8;
use Encode;
use Getopt::Long;
#====================================================================
my (%args) = (
);

GetOptions(
	'a=s' => \$args{"a"},
	'b=s' => \$args{"b"},
	'log=s' => \$args{"log"}
);
#====================================================================
binmode(STDIN, ":utf8");
binmode(STDOUT, ":utf8");
binmode(STDERR, ":utf8");
#====================================================================
main: {
	my (@data_a) = read_file($args{"a"});
	my (@data_b) = read_file($args{"b"});
	my (@data_log) = ( -e $args{"log"} ) ? read_file($args{"log"}) : ();

	for( my $i=0 ; $i<scalar(@data_a) ; $i++ ) {
		next if( !defined($data_b[$i]) );

		my (@t_a) = @{$data_a[$i]};
		my (@t_b) = @{$data_b[$i]};
		my (@t_log) = ( defined($data_log[$i]) ) ? @{$data_log[$i]} : ();

		my (@bleu_a) = @t_a[0..3];
		my (@bleu_b) = @t_b[0..3];

		next if( join(":", @bleu_a) eq join(":", @bleu_b) );

		my (@bleu) = ();
		for( my $j=0 ; $j<scalar(@bleu_a) ; $j++ ) {
			push(@bleu, sprintf("%#.4f", $bleu_b[$j]-$bleu_a[$j]));
		}

		my (@data) = ();

		push(@data, $t_a[4]); # tst
		push(@data, $t_b[4]); # tst

		push(@data, @t_b[5..$#t_b]); # src, ref

		push(@data, $t_log[1]) if( defined($t_log[1]) ); # log

		print join("\t", @bleu)."\t".join("\t", @data)."\n";
	}
}

#====================================================================
sub read_file {
	my ($fn) = (@_);

	print STDERR "Reading File: $fn\n";

	my (@ret) = ();

	unless( open(FILE, "<", $fn) ) {die "can not open : ".$!."\n"}
	binmode(FILE, ":utf8");
	
	foreach my $line ( <FILE> ) {
		$line =~ s/\s+$//;		

		my (@t) = split(/\t/, $line);

		push(@ret, \@t);
	}	
	close(FILE);

	return @ret;
}
#====================================================================
__END__      



cat WIT.en-ko.short.sentbleu_tuning/script_test.n3_0.1.model/model.0/data/test.en-ko.out \
   | perl ./matching_unknown.pl -dict extraction/out/T06.dict.txt \
   > WIT.en-ko.short.sentbleu_tuning/script_test.n3_0.1.model/model.0/data/test.en-ko.out.dict_apply

# 34/430

export tools=`pwd`
export SCRIPTS_ROOTDIR=~/vols/vol1/tools/mosesdecoder/scripts

export data_path=WIT.en-ko.short.sentbleu_tuning/script_test.n3_0.1.model/model.0/data
export test_set=test

export src=en
export trg=ko

perl $tools/wrap.pl -type src \
  -in $data_path/$test_set.$src-$trg.$src \
  -out $data_path/$test_set.$src-$trg.$src.sgm

perl $tools/wrap.pl -type ref \
  -in $data_path/$test_set.$src-$trg.$trg \
  -out $data_path/$test_set.$src-$trg.$trg.sgm

perl $tools/wrap.pl -type tst \
  -in $data_path/$test_set.$src-$trg.out.dict_apply \
  -out $data_path/$test_set.$src-$trg.out.sgm

sync

$SCRIPTS_ROOTDIR/mteval-v11b.pl \
  -s $data_path/$test_set.$src-$trg.$src.sgm \
  -r $data_path/$test_set.$src-$trg.$trg.sgm \
  -t $data_path/$test_set.$src-$trg.out.sgm \
  | tee $data_path/$test_set.$src-$trg.out.bleu

sync



