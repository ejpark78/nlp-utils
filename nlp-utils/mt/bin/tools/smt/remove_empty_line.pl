#!/usr/bin/perl
#====================================================================
use strict;
use Encode;
use FileHandle;
use File::Path;
use Getopt::Long;
use POSIX;
use Data::Dumper;
#====================================================================
my (%args) = (
	"src" => "",
	"trg" => "",
);

GetOptions(
	"uniq|unique" => \$args{"unique"},
	"src=s" => \$args{"src"},
	"trg=s" => \$args{"trg"},
);
#====================================================================
# MAIN
#====================================================================
main: {
	binmode(STDIN, ":utf8");
	binmode(STDOUT, ":utf8");
	binmode(STDERR, ":utf8");

	my (%unique) = ();

	if( $args{"src"} ne "" && -e $args{"src"} ) {
		die "can not open $!\n" unless( open(FILE_A, $args{"src"}) );
		die "can not open $!\n" unless( open(FILE_B, $args{"trg"}) );

		binmode(FILE_A, ":utf8");
		binmode(FILE_B, ":utf8");	

		foreach my $line_a ( <FILE_A> ) {
			my $line_b = <FILE_B>;

			print_result($line_a, $line_b, \%unique);
		}

		close(FILE_A);
		close(FILE_B);
	} else {
		while( my $line=<STDIN> ) {
			$line =~ s/\s+$//;

			my ($line_a, $line_b) = split(/\t/, $line, 2);
			print_result($line_a, $line_b, \%unique);
		}
	}
}
#====================================================================
sub print_result {
	my $line_a = shift(@_);
	my $line_b = shift(@_);
	my $unique = shift(@_);

	$line_a =~ s/^\s+|\s+$//g;
	$line_b =~ s/^\s+|\s+$//g;

	if( $line_a eq "" || $line_b eq "" ) {
		printf STDERR "# EMPTY\t[%s]\t[%s]\n", $line_a, $line_b;
		next;
	}

	return if( $line_a eq $line_b );

	my $result = sprintf("%s\t%s", $line_a, $line_b);
	if( $args{"unique"} ) {
		if( !defined($unique->{$result}) ) {
			print $result."\n";
		} else {
			printf STDERR "# unique\t%s\t%s\n", $line_a, $line_b;
		}

		$unique->{$result} = 1;
	} else {
		print $result."\n";				
	}
}
#====================================================================
__END__

