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
	"seq|sequence=s" => \$args{"sequence"},
	"debug" => \$args{"debug"}
);
#====================================================================
# MAIN
#====================================================================
main: {
	parse_lbmt_xml_log(\%args);	
}
#====================================================================
# sub functions
#====================================================================
sub parse_lbmt_xml_log {
	binmode(STDIN, ":utf8");
	binmode(STDOUT, ":utf8");
	binmode(STDERR, ":utf8");

	my (%param) = (%{shift(@_)});
	my (%seq) = parse_sequence($param{"sequence"});

	if( $param{"debug"} ) {
		foreach my $k ( keys %param ) {
			print STDERR "# param: $k => ".$param{$k}."\n";
		}
	}

	my $tag = "translated_sentence";

	while( my $line = <STDIN> ) {
		$line =~ s/\s+$//;

		next if( $line eq "" );

		my (@t) = split(/\t/, $line);
		my $src = $t[$seq{"src"}];
		my $xml = $t[$seq{"xml"}];

		if( $xml =~ /<$tag>(.+?)<\/$tag>/ ) {
			print "$src\t$1\n";
		}
	}
}
#====================================================================
sub parse_sequence {
	my $sequence = shift(@_);

	my $idx = 0;
	my (%input_sequence) = ();
	foreach my $pos ( split(/,/, $sequence) ) {
		$input_sequence{$pos} = $idx;
		$idx++;
	}

	return (%input_sequence);
}
#====================================================================
__END__

