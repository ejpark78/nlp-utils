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
	"db" => "db.leveldb",
	"seq" => "ko-en"
);
GetOptions(
	"db=s" => \$args{"db"},
	"seq=s" => \$args{"seq"}
);
#====================================================================
# MAIN
#====================================================================
main: {
	binmode(STDIN, ":utf8");
	binmode(STDOUT, ":utf8");
	binmode(STDERR, ":utf8");

	my (%data) = ();

	my $line_no = 0;
	while( my $line=<STDIN> ) {
		$line =~ s/^\s+|\s+$//g;

		print STDERR "." if( $line_no++ % 100000 == 0 );
		printf STDERR "(%s)", comma($line_no) if( $line_no % 1000000 == 0 );

		my ($src, $trg) = split(/\t/, $line, 2);
		next if( !defined($trg) || !defined($src) );

		$src =~ s/^\s+|\s+$//g;
		next if( $src eq "" );

		$src =~ s/\s+/ /g;
		$trg =~ s/\s+/ /g;

		if( $args{"seq"} eq "ko-en" ) {
			$data{$trg} .= sprintf("%s\t%s\n", $src, $trg);
		} else { 
			# en-ko en-es
			$data{$src} .= sprintf("%s\t%s\n", $src, $trg);
		}
	}

	my $db = new Tie::LevelDB::DB($args{"db"});
	die("ERROR cannot open db: ", $args{"db"}) if( !defined($db) );

	foreach my $en ( keys %data ) {
		$db->Put($en, $data{$en});
	}

	# $db->Get($k)
}
#====================================================================
# sub functions
#====================================================================

#====================================================================
sub comma {
	my $cnt = shift(@_);

	$cnt = reverse join ",", (reverse $cnt) =~ /(\d{1,3})/g;

	return $cnt;
}
#====================================================================
__END__


