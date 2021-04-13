#!/usr/bin/perl
#====================================================================
use strict;
use Encode;
use Getopt::Long;
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

	my ($docid) = ("");
	my (%domain, %data) = ();

	foreach my $fn ( @ARGV ) {
		$fn =~ s/\s+$//;
		$fn =~ s/\*$//;

		my ($lang) = ($fn =~ m/\.(..)\.sgm/);
		($lang) = ($fn =~ m/\.(..)\.raw\.sgm/) if( !defined($lang) );

		# print STDERR "# fn: $fn, lang: $lang\n";

		unless( open(FILE, "<".$fn) ) {die "can not open ".$fn.": ".$!}
		binmode(FILE, "utf8");

		while( my $line=<FILE> ) {
			$line =~ s/^\s+|\s+$//g;

			# <srcset setid="test2008" srclang="any">
			# <doc docid="napi.hu/2007/12/12/0" genre="news" origlang="hu">
			# <seg id="1"> Food: Where European inflation slipped up </seg>

			# <refset trglang="en" setid="newstest2014" srclang="any">
			# <doc sysid="ref" docid="1009-lemondefr" genre="news" origlang="fr">
			# <seg id="1">Spectacular Wingsuit Jump Over Bogota</seg>

			if( $line =~ m/<doc/ ) {
				my ($id) = ($line =~ m/docid="(.+?)"/);
				my ($genre) = ($line =~ m/genre="(.+?)"/);
				my ($origlang) = ($line =~ m/origlang="(.+?)"/);
				my ($sysid) = ($line =~ m/sysid="(.+?)"/);

				$docid = $id if( defined($id) );

				$domain{$genre} = $genre;
				# $domain{$docid} = "genre=$genre, origlang=$origlang, sysid=$sysid";
				# print STDERR $domain{$docid}."\n";
			}

			if( $line =~ m/<seg/ ) {
				my ($segid, $text) = ($line =~ m/<seg id="(\d+)">(.+)<\/seg>/);

				push(@{$data{$docid}{$segid}{$lang}}, $text);
			}
		}		

		close(FILE);
	}

	foreach my $docid ( sort keys %data ) {
		foreach my $segid ( sort keys %{$data{$docid}} ) {
			my (@en) = @{$data{$docid}{$segid}{"en"}};
			# my (@es) = @{$data{$docid}{$segid}{"es"}};
			my (@fr) = @{$data{$docid}{$segid}{"fr"}};

			# printf "%d\t%d\n", scalar(@en), scalar(@fr);
			# printf "%d\t%d\t%d\n", scalar(@en), scalar(@es), scalar(@fr);

			printf "%s\t%s\n", join(" ", @en), join(" ", @fr);
			# printf "%s\t%s\t%s\n", join(" ", @en), join(" ", @es), join(" ", @fr);
		}
	}

	printf STDERR "genre: %s\n", join(", ", keys %domain);
}
#====================================================================
# sub functions
#====================================================================
#====================================================================
__END__

