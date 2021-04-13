#!/usr/bin/perl -w
#====================================================================
# usage: perl $scripts/wget_pdf.pl < mtm2010.htm | sh -
#====================================================================
use strict;
use utf8;

use HTML::TokeParser;

use Getopt::Long;
#====================================================================
my (%args) = (
	test => "",
);

GetOptions(
	'test=s' => \$args{test},
);
#====================================================================
#binmode(STDIN, ":utf8");
#====================================================================

my $buf = "";
foreach my $line ( <STDIN> ) {
	$line =~ s/\s+$/ /;
	
	$buf .= $line;	
}

ParseHtml($buf);

#====================================================================
sub ParseHtml
{
	my ($_html) = @_;
	
	my $p = HTML::TokeParser->new(\$_html) || return "";
	
	my $cnt = 1;
	my (%link) = ();
	while( my $token = $p->get_token ) {
		my ($ttype, $tag, $attr, $attrseq, $rawtxt) = @{$token};

		# start tag			
		if( $ttype eq "S" ) { 
			if( $tag eq "a" ) {
				my $href = $attr->{href};

				my $fn = $href;
				$fn =~ s/^.+\/(.+?)$/$1/;
				
				chomp($href);
				
				my $fn_out = sprintf("%03d.%s", $cnt++, $fn);
				
#				my $fn_out2 = $p->get_trimmed_text("/".$tag);				
#				print "mv \"$fn_out\" \"$fn_out2\"\n";
				
				print "wget -c \"$href\" -O \"$fn_out\"\n";		
				
				$link{$href} = $fn_out;
			}
		}
	}

	foreach my $href ( keys %link ) {
		$_html =~ s/$href/$link{$href}/g;	
	}
	
#	$_html =~ s/></>\n</g;
	$_html =~ s/<\/p>/<\/p><br>\n/g;
	
	print STDERR $_html;

#	return ($buf);
}
#====================================================================
#====================================================================
__END__


cat log.html | perl ../test.pl | sh -  

gs -dNOPAUSE -sDEVICE=pdfwrite -sOUTPUTFILE=firstANDsecond.pdf -dBATCH first.pdf second.pdf

