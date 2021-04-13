#!/usr/bin/perl -w

use strict;

# use lib "$ENV{TOOLS}/bin";
# require "base_lib.pm";


sub get_file_size {
	my $f = shift(@_);
	my $file_type = shift(@_);

	$file_type = `file $f` if( !defined($file_type) );

	my $size = 0;
	if( $file_type eq "gzip" || $file_type =~ m/ gzip compressed data,/ ) {
		$size = `zcat $f | wc -l`;
	} else {
		$size = `wc -l $f`;
	}

	$size =~ s/\s+$//;

	return $size;
}


sub get_progress_str {
	my $i = shift(@_);
	my $total = shift(@_);
	my $start = shift(@_);

	my $t_passed = time() - $start;
	my $t_left = 0;
	$t_left = ($total - $i) * ($t_passed / $i) if( $i > 0 );
	
	$total = 1 if( $total == 0 );

	return sprintf("%s / %s (%.1f%%), time: %s / %s", 
			comma($i), comma($total), ($i/$total) * 100, sec2str($t_passed), sec2str($t_left));
}


sub sec2str {
	my $sec = shift(@_);

	my $d = int($sec/86400);
	my $h = ($sec/3660) % 24;
	my $m = ($sec/60) % 60;
	my $s = $sec % 60;

	return sprintf("%d days %02d:%02d:%02d", $d, $h, $m, $s) if( $d > 0 );

	return sprintf("%02d:%02d:%02d", $h, $m, $s) if( $h > 0 );

	return sprintf("%02d:%02d", $m, $s) if( $m > 0 );

	return sprintf("%02d", $s);
}


sub comma {
	my $cnt = shift(@_);

	$cnt = sprintf("%d", $cnt);
	for ( my $i = -3; $i > -1 * length($cnt); $i -= 4 ){
	    substr( $cnt, $i, 0 ) = ',';
	}

	return $cnt;
}


1

__END__
