#!/usr/bin/perl
#====================================================================
use strict;
use Encode;
use FileHandle;
use File::Path;
use Getopt::Long;
use POSIX;
#====================================================================
my (%args) = (
	"prefix" => "nbest."
);

GetOptions(
	"prefix=s" => \$args{"prefix"}
);
#====================================================================

main:{
#0 ||| Si no me equivoco , ha estado funcionando más de dos años .  ||| LexicalReordering0= -0.361944 0 0 -0.535679 0 0 Distortion0= 0 LM0= -38.8966 WordPenalty0= -13 PhrasePenalty0= 6 TranslationModel0= -7.32646 -21.9916 -6.37963 -19.1174 ||| -16.4806
#1 ||| ¿ Hay un concierto en algún lugar ?  ||| LexicalReordering0= -1.0284 0 0 -1.30201 0 0 Distortion0= 0 LM0= -29.0019 WordPenalty0= -8 PhrasePenalty0= 6 TranslationModel0= -12.1297 -18.9212 -3.97544 -9.39044 ||| -14.8834

	my (%data) = ();

	while( my $line=<STDIN> ) {
		$line =~ s/^\s+|\s+$//g;

		my ($s_id, $trg) = split(/ \|\|\| /, $line);
		next if( $s_id eq "" );

		push(@{$data{$s_id}}, $trg);
	}
	
	my (@fp) = ();
	for( my $i=0 ; $i<scalar @{$data{"0"}} ; $i++ ){
		my $fn = $args{"prefix"}.$i;
		#print "fn: $fn\n";
		open($fp[$i], ">", $fn);
	}

	foreach my $s_id ( sort {$a<=>$b} keys %data ) {
		#printf "$s_id:%d\n", scalar(@{$data{$s_id}});
		for( my $i=0 ; $i<scalar(@{$data{$s_id}}) ; $i++ ){
		#	print "$s_id \t $i \n";
			printf { $fp[$i] } "%s\n", $data{$s_id}[$i];	
		}
	}

	for( my $i=0 ; $i<scalar @fp ; $i++ ){
		close($fp[$i]);
	}
		
}
#====================================================================

__END__

