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
use lib "$ENV{TOOLS}";
require "base_lib.pm";
#====================================================================
my (%args) = (
	"l1" => 0,
	"l2" => 1,
);

GetOptions(
	"l1=i" => \$args{"l1"},
	"l2=i" => \$args{"l2"},
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

		printf STDERR "." if( $cnt++ % 10000 == 0 );
		printf STDERR "(%s)\n", comma($cnt) if( $cnt % 100000 == 0 );

		my (@token) = split(/\t/, $line);

		my $a = $token[$args{"l1"}];
		my $b = $token[$args{"l2"}];

		next if( $a =~ /^\s*$/ || $b =~ /^\s*$/ );

		$a =~ s/\/\// /g;
		$b =~ s/\/\// /g;

		$a =~ s/-/\t/g;
		$b =~ s/-/\t/g;
		
		$a =~ s/^\s+|\s+$//g;
		$b =~ s/^\s+|\s+$//g;

		$a = clean_text($a);
		$b = clean_text($b);
		
		next if( $a =~ /^\s*$/ || $b =~ /^\s*$/ );
		next if( $a eq $b );

		$token[$args{"l1"}] = $a;
		$token[$args{"l2"}] = $b;

		printf "%s\n", join("\t", @token);
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

	$text =~ s// /g;
	$text =~ s/\“+/\"/g;
	$text =~ s/\”+/\"/g;
	$text =~ s/\？+/\?/g;
	$text =~ s/\"+/\"/g;
	$text =~ s/\'+/\'/g;
	$text =~ s/^-//g;
	$text =~ s/^!//g;
	$text =~ s/♪/ /g;	

	$text =~ s/^\s*\"(.+)\"\s*$/$1/;
	$text =~ s/^\s*\'(.+)\'\s*$/$1/;
	$text =~ s/^\s*\#|\#\s*$//g;

	$text =~ s/ -/ /g;
	$text =~ s/\s+/ /g;

	$text =~ s/^.+? -> .+?,\s*//;

	$text =~ s/^\s+|\s+$//g;

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

