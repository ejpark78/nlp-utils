#!/usr/bin/perl -w
#====================================================================
use strict;
use utf8;
use Getopt::Long;
use File::Basename;
use File::MimeInfo;
use Cwd qw/ realpath /;
use FindBin qw($RealBin);
use File::Path;
#====================================================================
my (%args) = (
);

GetOptions(
	"f|in=s" => \$args{"in"},
	"prefix=s" => \$args{"prefix"},
);
#====================================================================
binmode(STDIN, ":utf8");
binmode(STDOUT, ":utf8");
#====================================================================
main: {
	unless( $args{"prefix"} ) {
		$args{"prefix"} = $args{"in"}.".";
	}

	cut_eval_set($args{"in"}, $args{"prefix"});
}
#====================================================================
sub cut_eval_set {
	my $f_in = shift(@_);
	my $f_prefix = shift(@_);

	#my ($src, $trg) = ($f_in =~ m/(..)(..)$/);
	my ($src, $trg) = ("src", "ref");

	my $row = 0;
	my (@data) = ();

	unless( open(FILE_IN, "<".$f_in) ) {die "can not open ".$f_in.": ".$!}
	binmode(FILE_IN, "utf8");

	foreach my $line ( <FILE_IN> ) {
		$line =~ s/\s+$//;

		my (@cols) = split(/\t/, $line);
		for( my $i=0 ; $i<scalar(@cols) ; $i++ ) {
			$data[$i][$row] = $cols[$i];
		}
		$row++;
	}

	close(FILE_IN);

	# save
	for( my $i=0 ; $i<scalar(@data) ; $i++ ) {		
		my $fn = "";

		if( $i == 0 ) {
			$fn = $f_prefix.$src;
		} else {
			$fn = $f_prefix.$trg."$i";
		}		

		rmdir($fn);
		save_file($fn, \@{$data[$i]});
	}	
}
#====================================================================
sub save_file {
	my $f_out = shift(@_);
	my (@data) = (@{shift(@_)});

	unless( open(FILE_OUT, ">".$f_out) ) {die "can not open ".$f_out.": ".$!}
	binmode(FILE_OUT, "utf8");

	print FILE_OUT join("\n", @data)."\n";

	close(FILE_OUT);
	FILE_OUT->autoflush(1);
}
#====================================================================
__END__
