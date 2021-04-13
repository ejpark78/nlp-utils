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
	's|seg=s' => \$args{"seg"},
	'with_tag' => \$args{"with_tag"},
	'plan_text' => \$args{"plan_text"}
);
#====================================================================
binmode(STDIN, ":utf8");
binmode(STDOUT, ":utf8");
#====================================================================
main: {
	my (@seg) = ();
	
	unless( open(SEG_RESULT, "<", $args{"seg"}) ) {
		die "can not open ".$args{"seg"}.": ".$!."\n"
	}

	binmode(SEG_RESULT, ":utf8");	
	foreach my $line ( <SEG_RESULT> ) {
		$line =~ s/\s+$//;		
		push(@seg, $line);
	}	
	close(SEG_RESULT);

	my $s = "";
	my $prev_pos = "";
	my (@buf) = ();
	
	while( my $line = <STDIN> ) {
		$line =~ s/\s+$//;
		
		my ($w) = split(/ /, $line, 2);

		my $seg_item = shift(@seg);

		next if( !defined($seg_item) );
		my ($t, $pos) = split(/-/, $seg_item);

		$w = "" if( !defined($w) );
		$t = "" if( !defined($t) );
		
		if( $w eq "" ) {
			if( $s ne "" ) {
				if( !$args{"plan_text"} ) {
					$s .= " $prev_pos .";
				} elsif( $args{"with_tag"} ) {
					$s .= "/$prev_pos";
				}
				push(@buf, $s);
				$s = "";
			}
			
			my $sep = "\n";
			$sep = " " if( $args{"plan_text"} );
			
			print join($sep, @buf)."\n";
			print "\n" if( !$args{"plan_text"} );
			
			(@buf) = ();
			next;
		}
		
		if( $t eq "B" && $s ne "" ) {
			if( !$args{"plan_text"} ) {
				$s .= " $pos .";
			} elsif( $args{"with_tag"} ) {
				$s .= "/$prev_pos";
			}
			push(@buf, $s);
			$s = "";
		}

		$s .= $w;	

		$prev_pos = $pos;	
	}
	
	print "\n";
		
}

#====================================================================
__END__