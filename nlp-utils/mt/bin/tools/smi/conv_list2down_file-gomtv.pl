#!/usr/bin/perl
#====================================================================
use strict;
use Encode;
use FileHandle;
use File::Path;
use POSIX;
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
			next if( $line !~ /&menu=subtitles&seq=/ );
			next if( $line =~ /txt_noti/ );

			$line =~ s/ href=\"/\n/ms; 
			$line =~ s/" title="/\n/ms;

			foreach my $url ( split(/\n/, $line) ) {
				next if( $url !~ /^\/main\/index/ );

				$url = "http://gom.gomtv.com/".$url;
				push(@url_list, $url);
			}
		}

		close(FILE);
		
		my $cmd = "";
		foreach my $url ( @url_list ) {
			# print "$url\n";
			my $fn_html = download_page($url);
			download_smi($fn_html);
		}
	}
}
#====================================================================
# sub functions
#====================================================================
sub download_page {
	my $url = shift(@_);

	my $seq_id = "";
	$seq_id = $1 if( $url =~ m/seq=(\d+)/ );

	my $fn_html = sprintf("page/%s.html", $seq_id);

	if( !-e $fn_html ) {
		my $cmd = "";
		$cmd .= sprintf("wget --quiet --user-agent=\"%s\" ", "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)");
		# $cmd .= sprintf("--cookies=on --keep-session-cookies --save-cookies=page/%s.cookies ", $seq_id);
		$cmd .= sprintf("\"%s\" -O \"%s\"", $url, $fn_html);
		$cmd .= sprintf(";sleep %f;sync", 2+rand(3));

		safesystem($cmd);
	}

	return $fn_html;
}
#====================================================================
sub download_smi {
	my $fn = shift(@_);

	unless( open(FILE, "<", $fn) ) {}
	
	my (@func_list) = ();

	foreach my $line ( <FILE> ) {
		next if( $line !~ /onclick="downJm\(/ );

		$line =~ s/downJm\(\'/\ndownJm\t/ms; 
		$line =~ s/\'\); /\n/ms;

		foreach my $func ( split(/\n/, $line) ) {
			next if( $func !~ /^downJm/ );

			$func =~ s/^downJm\s+//g;
			$func =~ s/\', \'/\t/g;

			$func = decode("utf8", $func);

			push(@func_list, $func);
		}
	}

	close(FILE);

	my $cmd = "";

	foreach my $func ( @func_list ) {
		print "# $func\n";

		my ($intSeq, $capSeq, $fileName) = split(/\t/, $func);

		next if( -d "file/$intSeq" );

		my $fn_smi = sprintf("file/%s/%s", $intSeq, $fileName);
		if( !-e $fn_smi ) {
			$cmd = sprintf("mkdir -p file/%s; sync", $intSeq);
			safesystem($cmd);

			$cmd = sprintf("wget --quiet \"http://gom.gomtv.com/main/index.html/%s\" ", $fileName);
			$cmd .= sprintf("--post-data \"ch=subtitles&pt=down&intSeq=%s&capSeq=%s\" ", $intSeq, $capSeq);
			$cmd .= sprintf("-O \"%s\"", $fn_smi);
			$cmd .= sprintf(";sleep %f", 2+rand(5));
			safesystem($cmd);
		}
	}
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


