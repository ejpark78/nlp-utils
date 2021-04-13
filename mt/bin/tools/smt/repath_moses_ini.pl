#!/usr/bin/perl -w
#====================================================================
use strict;
use utf8;
use Encode;
use Getopt::Long;
#====================================================================
my (%args) = ();

GetOptions(
	"lm" => \$args{"lm"}
);
#====================================================================
binmode(STDIN, ":utf8");
binmode(STDOUT, ":utf8");
binmode(STDERR, ":utf8");
#====================================================================
main: {
	while( my $fn=<STDIN> ) {
		$fn =~ s/\s+$//;

		printf "$fn\n";

		open(FH_IN, "<", $fn) || die "$!";
		my (@ini) = <FH_IN>;
		close(FH_IN);

		my $original = join("", @ini);

		my $path = $fn;
		$path =~ s/[^\/]+$//;

		if( $path =~ m/^\.\// ){
			my $pwd = $ENV{"PWD"};
			$path =~ s/^\.\//$pwd\//;
		}

		print "path: $path\n";

		# PhraseDictionaryBinary name=TranslationModel0 table-limit=20 num-features=4 path=/home/ejpark/workspace/model/en-es/subtitle-5M-1/bitext_filtering/similarty-based.n2.0.9/phrase-table.reduced input-factor=0 output-factor=0
		# LexicalReordering name=LexicalReordering0 num-features=6 type=wbe-msd-bidirectional-fe-allff input-factor=0 output-factor=0 path=/home/ejpark/workspace/model/en-es/subtitle-5M-1/bitext_filtering/similarty-based.n2.0.9/reordering-table.reduced 

		for( my $i=0 ; $i<scalar(@ini) ; $i++ ) {
			next if( $ini[$i] !~ /path=/ );
			next if( !defined($args{"lm"}) && $ini[$i] =~ /KENLM/ );

			$ini[$i] =~ s/path=(.+)\//path=$path/;
		}

		my $new_ini = join("", @ini);

		if( $original ne $new_ini ) {
			open(FH_OUT, ">", $fn) || die "$!";

#print $new_ini;
			print FH_OUT $new_ini;

			close(FH_OUT);
		}		
	}
}
#====================================================================
__END__      

find `pwd` -name '*.ini' | repath_moses_ini.pl 

