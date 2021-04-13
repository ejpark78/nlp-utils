#!/usr/bin/perl
#====================================================================
use strict;
use Encode;
use FileHandle;
use File::Path;
use Getopt::Long;
use Tie::LevelDB; 
use POSIX;
#====================================================================
my (%args) = (
);

GetOptions(
);
#====================================================================
# MAIN
#====================================================================
main: {
	binmode(STDIN, ":utf8");
	binmode(STDOUT, ":utf8");
	binmode(STDERR, ":utf8");

	my $cnt=0;
	while( my $line=<STDIN> ) {
		$line =~ s/^\s+|\s+$//g;

		print STDERR "." if( $cnt++ % 10000 == 0 );
		print STDERR "($cnt)" if( $cnt % 100000 == 0 );

		my ($a,$b) = split(/\t/, $line, 2);
		next if( $a =~ /^\s*$/ || $b =~ /^\s*$/ );

		$a =~ s/\/\// /g;
		$b =~ s/\/\// /g;

		$a =~ s/-/\t/g;
		$b =~ s/-/\t/g;
		
		$a =~ s/^\s+|\s+$//g;
		$b =~ s/^\s+|\s+$//g;

		my (@list_a) = split(/\t/, $a);
		my (@list_b) = split(/\t/, $b);

		# print ">> ".join("|", @list_a)." eq ".join("|", @list_b)."\n";
		if( scalar(@list_a) > 1 && scalar(@list_a) eq scalar(@list_b) ) {
			for( my $i=0 ; $i<scalar(@list_a) ; $i++ ) {
				my $aa = clean_text($list_a[$i]);
				my $bb = clean_text($list_b[$i]);

				$aa =~ s/\"/ /g if( $aa =~ /\"/ && $bb !~ /\"/ );
				$bb =~ s/\"/ /g if( $bb =~ /\"/ && $aa !~ /\"/ );
		
				next if( $aa =~ /^\s*$/ || $bb =~ /^\s*$/ );
				next if( $aa eq $bb );

				print "$aa\t$bb\n";
			}
		}

		$a = clean_text($a);
		$b = clean_text($b);

		$a =~ s/\"/ /g if( $a =~ /\"/ && $b !~ /\"/ );
		$b =~ s/\"/ /g if( $b =~ /\"/ && $a !~ /\"/ );
		
		next if( $a =~ /^\s*$/ || $b =~ /^\s*$/ );
		next if( $a eq $b );

		print "$a\t$b\n";
	}
}
#====================================================================
sub clean_text 
{
	my $text = shift(@_);

	$text = Encode::encode("utf8", $text);

	$text =~ s/\t+/ /g;

    $text =~ s/\&amp;/\&/g;   # escape escape
    # $text =~ s/\|/\&#124;/g;  # factor separator
    $text =~ s/\&lt;/\</g;    # xml
    $text =~ s/\&gt;/\>/g;    # xml
    $text =~ s/\&apos;/\'/g;  # xml
    $text =~ s/\&quot;/\"/g;  # xml
    $text =~ s/\&#91;/\[/g;   # syntax non-terminal
    $text =~ s/\&#93;/\]/g;   # syntax non-terminal
    $text =~ s/\\x92/\'/g;  

	$text =~ s/♪/ /g;	
	$text =~ s/♬/ /g;	
	$text =~ s/…/.../g;		
	$text =~ s/‘/'/g;				
	$text =~ s// /g;
	$text =~ s/\“+/\"/g;
	$text =~ s/\”+/\"/g;
	$text =~ s/\？+/\?/g;
	$text =~ s/^-//g;
	$text =~ s/^!//g;

	$text =~ s/\"+/\"/g;
	$text =~ s/\'+/\'/g;

	$text =~ s/^\s*\"(.+)\"\s*$/$1/;
	$text =~ s/^\s*\'(.+)\'\s*$/$1/;
	$text =~ s/^\s*\#|\#\s*$//g;

	$text =~ s/ -/ /g;
	$text =~ s/\s+/ /g;

	$text =~ s/^.+? -> .+?,\s*//;

	$text =~ s/^\s+|\s+$//g;

	# $text =~ s/(\w+)"re/$1're/g;
	# $text =~ s/(\w+)"m/$1'm/g;
	# $text =~ s/(\w+)"s/$1's/g;
	# $text =~ s/(\w+)"ll/$1'll/g;

	$text = Encode::decode("utf8", $text);	

	# print "[[$text]]\n";
	return $text;
}
# sub functions
#====================================================================
#====================================================================
__END__



    # $text =~ s/\&/\&amp;/g;   # escape escape
    # $text =~ s/\|/\&#124;/g;  # factor separator
    # $text =~ s/\</\&lt;/g;    # xml
    # $text =~ s/\>/\&gt;/g;    # xml
    # $text =~ s/\'/\&apos;/g;  # xml
    # $text =~ s/\"/\&quot;/g;  # xml
    # $text =~ s/\[/\&#91;/g;   # syntax non-terminal
    # $text =~ s/\]/\&#93;/g;   # syntax non-terminal

