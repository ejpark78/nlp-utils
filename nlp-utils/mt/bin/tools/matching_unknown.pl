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
	'dict=s' => \$args{"dict"}
);
#====================================================================
binmode(STDIN, ":utf8");
binmode(STDOUT, ":utf8");
binmode(STDERR, ":utf8");
#====================================================================
main: {
	my (%dict) = ();
	
	unless( open(DICT, "<", $args{"dict"}) ) {die "can not open : ".$!."\n"}
	binmode(DICT, ":utf8");
	
	foreach my $line ( <DICT> ) {
		$line =~ s/\s+$//;		

		my ($k, $e) = split(/\t/, $line, 2);

		# next if( !defined($e) );
		# next if( length($e) <= 3 );
		# next if( $k =~ /(다|운|스럽다|적인)$/ );
		
		# $e = lc($e);

		next if( defined($dict{$e}) );
		$dict{$e} = $k;
	}	
	close(DICT);

	my $c = 0;
	my $cnt = 0;
	
	while( my $line = <STDIN> ) {
		$line =~ s/\s+$//;
		
		my (@token) = split(/ /, $line);

		my $qoute = 0;

		my (@buf, @buf2, @dict_log) = ();
		for( my $i=0 ; $i<scalar(@token) ; $i++ ) {
			my $w = $token[$i];

			$qoute ^= 1 if( $w =~ /(\"|\')/ );

			# if( $qoute == 0 && $w =~ /^[A-Za-z]/ ) {
			if( $qoute == 0 && $w =~ /^[a-z]/ ) {
				# my $e = lc $w;
				my $e = $w;
					
				if( defined($dict{$e}) ) {
					$c++;	
					push(@buf, $dict{$e});
					push(@buf2, "<N>".$dict{$e}." <= ".$e."</N>");
					push(@dict_log, $dict{$e}." => ".$e);
				} else {
					push(@buf, $w);	
					push(@buf2, $w);
				}
				$cnt++;
			} else {
				push(@buf, $w);	
				push(@buf2, $w);
			}
		}
		
		my $trg = join(" ", @buf);
		print $trg."\n";
		print STDERR $trg."\t".join(";", @dict_log)."\n";
	}
	
	print STDERR "# $c/$cnt\n";
}

#====================================================================
__END__      


export home=WIT.en-ko/full_set.model/model.0
#export dict=extraction/out/T06.dict.txt
export dict=wiki/ko-en.all.txt
export tag=wiki_apply

cat $home/data/test.en-ko.out \
   | perl ./matching_unknown.pl -dict $dict \
   > $home/data/test.en-ko.out.$tag

# 34/430

export tools=`pwd`
export SCRIPTS_ROOTDIR=~/vol1/tools/mosesdecoder/scripts

export data_path=$home/data
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
  -in $data_path/$test_set.$src-$trg.out.$tag \
  -out $data_path/$test_set.$src-$trg.out.sgm

sync

$SCRIPTS_ROOTDIR/mteval-v11b.pl \
  -s $data_path/$test_set.$src-$trg.$src.sgm \
  -r $data_path/$test_set.$src-$trg.$trg.sgm \
  -t $data_path/$test_set.$src-$trg.out.sgm \
  | tee $data_path/$test_set.$src-$trg.out.$tag.bleu

sync



