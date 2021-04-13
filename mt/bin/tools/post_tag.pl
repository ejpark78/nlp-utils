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
	's|seg=s' => \$args{"seg"}
);
#====================================================================
binmode(STDIN, ":utf8");
binmode(STDOUT, ":utf8");
#====================================================================
main: {
	my (@seg) = ();
	
	unless( open(SEG_RESULT, "<", $args{"seg"}) ) {die "can not open ".$args{"seg"}.": ".$!."\n"}
	
	binmode(SEG_RESULT, ":utf8");
	
	foreach my $line ( <SEG_RESULT> ) {
		$line =~ s/\s+$//;
		
		push(@seg, $line);
	}
	
	close(SEG_RESULT);

	while( my $line = <STDIN> ) {
		$line =~ s/\s+$//;
		
		my ($w, $tt) = split(/ /, $line, 2);
		
		my $t = shift(@seg);
		
		if( !defined($w) || !defined($t) ) {
			print "\n";
			next;	
		}
		
		print "$w/$t ";
		
	}
	
	print "\n";
		
}

#====================================================================
__END__