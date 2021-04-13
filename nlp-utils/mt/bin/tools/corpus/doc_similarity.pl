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
);

GetOptions(
	"f=s" => \$args{"file"}
);
#====================================================================
# MAIN
#====================================================================
main: {
	binmode(STDIN, ":utf8");
	binmode(STDOUT, ":utf8");
	binmode(STDERR, ":utf8");

	print STDERR "loading dictionary \n";

	my $start_run = time();

	my $fn = $args{"file"};
	my ($open_mode, $file_type) = ("<", `file $fn`);

	$open_mode = "<:gzip" if( $file_type =~ m/ gzip compressed data,/ );
	die "can not open : $fn $!\n" unless( open(FILE, $open_mode, $fn) );

	my $cnt = 0;
	my (%ngram) = ();
	foreach my $str ( <FILE> ) {
		$str =~ s/\s+$//g;

		my ($w, $f) = split(/\t/, $str);		
		$ngram{$w} = $f;
		# printf "%s : = %d\n", $w, $f;

		printf STDERR "." if( $cnt++ % 100000 == 0 );
		printf STDERR "(%s, %02f)\n", comma($cnt), time() - $start_run if( $cnt % 3000000 == 0 );
	}

	close(FILE);

	print STDERR "\n";
	print STDERR "scanning corpus \n";

	$cnt = 0;
	while( my $line=<STDIN> ) {
		$line =~ s/^\s+|\s+$//g;

		my ($es, $en) = split(/\t/, $line, 2);
		my (@token) = split(/\s+/, $en);

		my $w_count = 0;
		my (@t) = get_str_ngram(\@token, 3);
		foreach my $w ( @t ) {
			$w_count++ if( defined($ngram{$w}) );			
		}

		my $sim = $w_count/scalar(@token);
		# printf "%f\t", $w_count/scalar(@token);
		printf "%s\n", $line if( @token < 3 || $sim > 0.9 );

		printf STDERR "." if( $cnt++ % 10000 == 0 );
		printf STDERR "(%s, %02f)\n", comma($cnt), time() - $start_run if( $cnt % 300000 == 0 );
	}
}
#====================================================================
# sub functions
#====================================================================
sub comma {
	my $cnt = shift(@_);

	$cnt = reverse join ",", (reverse $cnt) =~ /(\d{1,3})/g;

	return $cnt;
}
#====================================================================
sub get_str_ngram
{
	my (@token) = (@{shift(@_)});
	my $n = shift(@_);

	my (%ret) = ();

	$n--;

	for( my $i=0 ; $i<scalar($n) ; $i++ ) {
		unshift(@token, "<s>");
		push(@token, "</s>");
	}

	for( my $i=0 ; $i<scalar(@token)-$n ; $i++ ) {
		my $buf = join(" ", @token[$i..$i+$n]);

		$buf =~ s/\s+$//;

		next if( $buf eq "" );

		$ret{$buf} = 1;
	}

	return (keys %ret);
}
#====================================================================
__END__


