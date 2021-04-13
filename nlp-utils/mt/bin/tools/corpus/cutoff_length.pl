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
	"f=s" => \$args{"f"}
);
#====================================================================
# MAIN
#====================================================================
main: {
	binmode(STDIN, ":utf8");
	binmode(STDOUT, ":utf8");
	binmode(STDERR, ":utf8");

	die "can not open : ".$args{"f"}." $!\n" unless( open(FILE, $args{"f"}) );
	binmode(FILE, ":utf8");

	my (%cut_off) = ();
	foreach my $str ( <FILE> ) {
		$str =~ s/:\s+/\t/g;
		my (@t) = split(/\t/, $str);

		# 137	avg: 8.00	corrl: 0.00	cut_off: 000	0.000
		my $cnt_src = sprintf("%d", $t[0]);

		$cut_off{$cnt_src}{"avg"} = sprintf("%d", $t[2]);
		$cut_off{$cnt_src}{"std_var"} = sprintf("%d", $t[4]);

		printf STDERR "%d\t%3.5f\t%3.5f\n", 
			$cnt_src, $cut_off{$cnt_src}{"avg"}, $cut_off{$cnt_src}{"std_var"};
	}

	close(FILE);


	my $cnt = 0;
	while( my $line=<STDIN> ) {
		$line =~ s/^\s+|\s+$//g;

		printf STDERR "." if( $cnt++ % 100000 == 0 );
		printf STDERR "(%s)\n", comma($cnt) if( $cnt % 1000000 == 0 );

		my (@token) = split(/\t/, $line);

		my $a = $token[$args{"l1"}];
		my $b = $token[$args{"l2"}];

		next if( $a =~ /^\s*$/ || $b =~ /^\s*$/ );

    	my (@tok_a) = split(/\s+/, $a);
    	my (@tok_b) = split(/\s+/, $b);

    	my $cnt_src = scalar(@tok_a);
    	my $cnt_trg = scalar(@tok_b);

    	my $cut_off1 = $cut_off{$cnt_src}{"avg"} + $cut_off{$cnt_src}{"std_var"};
    	my $cut_off2 = $cut_off{$cnt_src}{"avg"} - $cut_off{$cnt_src}{"std_var"};

    	# print "$cnt_src, $cnt_trg, $cut_off1, $cut_off2, ".$cut_off{$cnt_src}{"avg"}."\n";

		# print STDERR "# ERROR a: $a\n";
		# print STDERR "# ERROR b: $b\n";

		# print STDERR "avg:".$cut_off{$cnt_src}{"avg"}.", ";
		# print STDERR "std_var:".$cut_off{$cnt_src}{"std_var"}.", ";
		# print STDERR "cnt_src:$cnt_src, ";
		# print STDERR "cnt_trg:$cnt_trg, ";
		# print STDERR "cut_off1:$cut_off1, ";
		# print STDERR "cut_off2:$cut_off2\n";

		if( $cnt_src > 50 || $cnt_trg > 50 ) {
    		# print STDERR "# ERROR: $line\n";
			next;
		}

		if( $cut_off{$cnt_src}{"std_var"} <= 0 ) {
    		# print STDERR "# ERROR: $line\n";
			next;
		}

		# $cut_off1 >= $cnt_trg >= $cut_off2
    	if( $cut_off2 <= $cnt_trg && $cnt_trg <= $cut_off1) {
	    	print "$line\n";
    	} else {
    		# print STDERR "# ERROR: $line\n";
    	}
	}
}
#====================================================================
# sub functions
#====================================================================
#====================================================================
__END__


