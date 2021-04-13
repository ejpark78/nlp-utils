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
	"simple" => \$args{"simple"},
	"debug" => \$args{"debug"}
);
#====================================================================
# MAIN
#====================================================================
main: {
	phrase_prob(\%args);	
}
#====================================================================
# sub functions
#====================================================================
sub phrase_prob {
	binmode(STDIN, ":utf8");
	binmode(STDOUT, ":utf8");
	binmode(STDERR, ":utf8");

	my (%param) = (%{shift(@_)});

	if( $param{"debug"} ) {
		foreach my $k ( keys %param ) {
			print STDERR "# param: $k => ".$param{$k}."\n";
		}
	}

	# open DB
	my ($f, $e, $align, @sent) = ();
	while( <STDIN> ) {
		s/\s+$//;

		# buffering phrase

		next if( $_ eq "" );

		if( /SOURCE: \[.+?\] (.+)$/ ) {
			$f = $1;
			next;
		} elsif( /TRANSLATED AS: (.+)\|?$/ ) {
			$e = $1;
			next;
		} elsif( /WORD ALIGNED: (.+)\|?$/ ) {
			$align = $1;

			my (%phrase) = ("src" => $f, "trg" => $e, "align" => $align);
			push(@sent, \%phrase);
			next;			
		} elsif( /SCORES \(UNWEIGHTED\/WEIGHTED\): / ) {
			my (@buf) = ();
			foreach my $k ( @sent ) {
				my (%phrase) = (%{$k});

				if( $param{"simple"} ) {
					push(@buf, sprintf("%s => %s", $phrase{"src"}, $phrase{"trg"}));
				} else {
					push(@buf, sprintf("%s ||| %s ||| %s", $phrase{"src"}, $phrase{"trg"}, $phrase{"align"}));
				}
			}

			if( $param{"simple"} ) {
				print join("; ", @buf)."\n";
			} else {
				print join(" <|||> ", @buf)."\n";
			}

			(@sent) = ();

			next;
		}

		$f = $e = $align = "";
	}
}
#====================================================================
__END__

