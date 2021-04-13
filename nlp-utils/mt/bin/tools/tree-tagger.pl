#!/usr/bin/perl
#====================================================================
use strict;
use Encode;
use FileHandle;
use Lingua::TreeTagger;
use Getopt::Long;
#====================================================================
my (%args) = (	
);

GetOptions(
	'language=s' => \$args{"language"},
	'pos' => \$args{"pos"},
	'tools=s' => \$args{"tools"},
);
#====================================================================
# MAIN
#====================================================================
main: {
	treetagger(\%args);	
}
#====================================================================
# sub functions
#====================================================================
sub treetagger {
	my (%param) = (%{shift(@_)});

	my $tools = $param{"tools"};
	my $path = "$tools/TreeTagger";

	my $tagger = Lingua::TreeTagger->new(
		'language' => $param{"language"},
		'options'  => [ qw( -token -lemma -sgml ) ],
	);
	
	while( <STDIN> ) {
		my $tagged_text = $tagger->tag_text( \$_ );
		# print $tagged_text->as_text()."\n";

		my (@buf) = ();
		foreach my $token ( @{ $tagged_text->sequence() } ) {
			if( $param{"pos"} ) {
				push(@buf, $token->original()."/".$token->tag());
			} else {
				push(@buf, $token->original());
			}
			# print $token->original(), '|', $token->tag(), "\n";
		}		

		print join(" ", @buf)."\n";
	}
}
#====================================================================
sub safesystem {
	print STDERR "Executing: @_\n";

	system(@_);

	if ($? == -1) {
		print STDERR "Failed to execute: @_\n  $!\n";
		exit(1);
	} elsif ($? & 127) {
		printf STDERR "Execution of: @_\n  died with signal %d, %s coredump\n", ($? & 127),  ($? & 128) ? 'with' : 'without';
		exit(1);
	}
	else {
		my $exitcode = $? >> 8;
		print STDERR "Exit code: $exitcode\n" if $exitcode;
		return ! $exitcode;
	}
}
#====================================================================
__END__

