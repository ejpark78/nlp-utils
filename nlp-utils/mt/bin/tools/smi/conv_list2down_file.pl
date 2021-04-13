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
	"login" => \$args{"login"}
);
#====================================================================
# MAIN
#====================================================================
main: {
	binmode(STDIN, ":utf8");
	binmode(STDOUT, ":utf8");
	binmode(STDERR, ":utf8");

	my $cmd = "";

	if( $args{"login"} ) {
		$cmd = "wget --user-agent=\"Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)\" ";
		$cmd .= "--cookies=on --keep-session-cookies --save-cookies page/login.cookie ";
		$cmd .= "--post-data 'mb_id=ejbb&mb_password=dlcjs' http://cineaste.co.kr/bbs/login_check.php";
		
		safesystem($cmd);
	}

	foreach my $line ( <STDIN> ) {
		$line =~ s/href=.\.\.\//\n/g;  
		$line =~ s/<\/span>/\n/g; 

		# print $line;

		foreach my $l ( split(/\n/, $line) ) {
			next if( $l !~ /wr_id/ );
			next if( $l !~ /^bbs/ );

			$l =~ s/.><span.+>/\t/; 

			my ($url) = split(/\t/, $l); 
			my ($wr_id) = ($url =~ m/wr_id=(\d+)/); 

			# print $l, "\t", $url, "\t", $wr_id, "\n";

			my $fn = sprintf("page/%s", $wr_id);

			next if( -e $fn.".html" );

			$cmd = sprintf("wget --user-agent=\"%s\" ", "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)");
			$cmd .= sprintf("--cookies=on --keep-session-cookies --save-cookies=%s.cookie ", $fn);

			if( $args{"login"} ) {
				$cmd .= sprintf("--load-cookies=page/login.cookie ");
			}

			$cmd .= sprintf("\"http://cineaste.co.kr/%s\" -O \"%s.html\"", $url, $fn);
			$cmd .= sprintf(";sleep %f; sync", 2+rand(3));

			safesystem($cmd);

			my ($wr, @url_list) = get_file_list($fn.".html");

			next if( scalar(@url_list) <= 0 );

			$cmd = sprintf("mkdir -p file/%s; sync", $wr_id);
			safesystem($cmd);

			foreach my $u ( @url_list ) {
				my ($url, $smi) = split(/\t/, $u);

				$smi = decode("utf8", $smi);

				$url =~ s/download\.php/download2\.php/;

				my $fn_smi = sprintf("file/%s/%s", $wr_id, $smi);

				next if( -e $fn_smi );

				print "\n\n$url\n$fn_smi\n\n";

				$cmd = sprintf("wget --user-agent=\"%s\" ", "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)");

				$cmd .= sprintf("--cookies=on --keep-session-cookies  ");
				$cmd .= sprintf("--load-cookies=%s.cookie ", $fn);
				$cmd .= sprintf("--referer=\"%s\" \"%s\" -O \"%s\";", $wr, $url, $fn_smi);
				$cmd .= sprintf("sleep %f", 2+rand(5));

				safesystem($cmd);
			}
		}
	}
}
#====================================================================
# sub functions
#====================================================================
sub get_file_list {
	my $fn = shift(@_);

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

	return ($wr, @url_list);
}
#====================================================================
sub comma {
	my $cnt = shift(@_);

	$cnt = reverse join ",", (reverse $cnt) =~ /(\d{1,3})/g;

	return $cnt;
}
#====================================================================
sub safesystem {
	print STDERR "Executing: @_\n\n";

	system(@_);

	if( $? == -1 ) {
		print STDERR "Failed to execute: @_\n  $!\n";
		exit(1);
	} elsif( $? & 127 ) {
		printf STDERR "Execution of: @_\n  died with signal %d, %s coredump\n", ($? & 127),  ($? & 128) ? 'with' : 'without';
		exit(1);
	} else {
		my $exitcode = $? >> 8;
		print STDERR "Exit code: $exitcode\n" if $exitcode;
		return ! $exitcode;
	}
	
	print STDERR "\n";
}
#====================================================================
__END__


