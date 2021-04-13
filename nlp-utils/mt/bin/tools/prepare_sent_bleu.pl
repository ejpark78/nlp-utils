#!/usr/bin/perl
#====================================================================
use strict;
use Encode;
use FileHandle;
use File::Path;
use IPC::Open2;
use PerlIO::gzip;
use Getopt::Long;
#====================================================================
my (%args) = (	
);

GetOptions(
	"src|s=s" => \$args{"src"}, 	
	"tst|t=s" => \$args{"tst"}, 	
	"ref|r=s" => \$args{"ref"}, 	
);
#====================================================================
# MAIN
#====================================================================
main: {
	my $fn_tst = $args{"tst"};
	my $fn_ref = $args{"ref"};
	my $fn_src = $args{"src"};

	die "can not open : ".$fn_tst." ".$!."\n" unless( open(TST, $fn_tst) );
	die "can not open : ".$fn_ref." ".$!."\n" unless( open(REF, $fn_ref) );
	die "can not open : ".$fn_src." ".$!."\n" unless( open(SRC, $fn_src) );

	foreach my $tst ( <TST> ) {
		my $src = <SRC>;
		my $ref = <REF>;

		$src = "" if( !defined($src) );
		$ref = "" if( !defined($ref) );
				
		$tst =~ s/\r?\n$//;	
		$src =~ s/\r?\n$//;	
		$ref =~ s/\r?\n$//;	
		
		next if( $tst eq "" || $ref eq "" || $src eq "" );

		print "<SRC>$src</SRC><TST>$tst</TST><REF>$ref</REF>\n";
	}	
	
	close(TST);
	close(REF);
	close(SRC);
}
#====================================================================
# sub functions
#====================================================================
__END__

-status

vocabulary size
total number of words

