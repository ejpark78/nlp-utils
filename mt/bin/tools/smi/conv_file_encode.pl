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
my (%args) = (
);

GetOptions(
);
#====================================================================
# MAIN
#====================================================================
main: {
	binmode(STDIN, ":utf8");
	binmode(STDOUT, ":utf8");
	binmode(STDERR, ":utf8");

	if (!@ARGV) {
	    @ARGV = <STDIN>;
	    chop(@ARGV);
	}

	foreach my $fn ( @ARGV ) {
		$fn =~ s/^\s+|\s+$//g;

		print STDERR "# $fn\n";

		my $list = "";
		unless( open(FILE, "<", $fn) ) {}
		
		my $wr = "";
		my (@url_list) = ();

		foreach my $line ( <FILE> ) {
			next if( $line !~ /file_download/ );

			$line =~ s/.\);/\n/ms; 
			$line =~ s/file_download\(.\.\//\n/ms; 
			$line =~ s/., ./\t/ms;

			foreach my $url ( split(/\n/, $line) ) {
				next if( $url !~ /^download\.php/ );

				($wr) = split(/\t/, $url, 2);

				$url = "http://cineaste.co.kr/bbs/".$url;
				push(@url_list, $url);
			}
		}

		close(FILE);

		next if( $wr eq "" );
		
		$wr = "http://cineaste.co.kr/bbs/".$wr;
		$wr =~ s/&no=\d+&/&/;
		$wr =~ s/download\.php/board\.php/;

		my $wr_id = "";
		$wr_id = $1 if( $wr =~ m/wr_id=(\d+)/ );
		
		# printf "wget ";
		# printf "--user-agent=\"%s\" ", "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)";
		# printf "--cookies=on --keep-session-cookies --save-cookies=cookie/%s.txt ", $wr_id;
		# printf "\"%s\" ", $wr;
		# printf "-O \"wr2/%s\"\n", $wr_id;

		# printf "sleep 20\n\n";
		foreach my $line ( @url_list ) {
			my ($url, $smi) = split(/\t/, $line);

			$smi = decode("utf8", $smi);

			print "file/$smi\n";

			# printf "wget ";
			# printf "--user-agent=\"%s\" ", "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)";
			# printf "--cookies=on --keep-session-cookies --load-cookies=cookie/%s.txt ", $wr_id;
			# printf "--referer=\"%s\" ", $wr;
			# printf "\"%s\" ", $url;
			# printf "-O \"file/%s\"\n", $smi;
			# printf "sleep 20\n\n";
		}
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
__END__


