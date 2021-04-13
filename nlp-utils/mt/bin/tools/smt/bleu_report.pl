#!/usr/bin/env perl
#!/usr/bin/perl
#====================================================================
use strict;
use Encode;
use utf8;
use Getopt::Long;
#====================================================================
my (%args) = (
	"col" => ".tok."
);

GetOptions(
	"col=s" => \$args{"col"},
	"debug" => \$args{"debug"}
);
#====================================================================
# MAIN
#====================================================================
main: {
	binmode(STDIN, "utf8");
	binmode(STDOUT, "utf8");
	binmode(STDERR, "utf8");

	my $col = $args{"col"};

	my (%buf) = ();
	while( my $line = <STDIN> ) {
		$line =~ s/\s+$//;

		next if( $line eq "" );

		$line =~ s/.bleu:NIST score = /\t/; 
		$line =~ s/\s+ BLEU score = /\t/; 
		$line =~ s/for system "0"/\t/; 
		$line =~ s.$col.\t.;

		my (@t) = split(/\t/, $line);

		if( scalar(@t) == 4 ) {
			$buf{$t[0]}{$t[1]}{"NIST"} = $t[2];
			$buf{$t[0]}{$t[1]}{"BLEU"} = $t[3];
		}

		print $line."\n";
	}
	print "\n";

	# print result
	my (@title) = get_title(\%buf);

	print_score(\@title, \%buf, "BLEU");
	print_score(\@title, \%buf, "NIST");
}
#====================================================================
# sub functions
#====================================================================
sub print_score {
	my (@title) = (@{shift(@_)});
	my (%buf) = (%{shift(@_)});
	my $tag = shift(@_);

	printf "%s\t%s\n", $tag, join("\t", @title);
	foreach my $tst ( sort keys %buf ) {
		my (@row) = ();

		push(@row, $tst);
		foreach my $col ( @title ) {
			if( !defined($buf{$tst}{$col}) || !defined($buf{$tst}{$col}{$tag}) ) {
				$buf{$tst}{$col}{$tag} = "";
			}

			push(@row, $buf{$tst}{$col}{$tag});
		}

		printf "%s\n", join("\t", @row);
	}

	print "\n";
}
#====================================================================
sub get_title {
	my (%buf) = (%{shift(@_)});

	my (%title_uniq) = ();
	foreach my $tst ( sort keys %buf ) {
		foreach my $col ( sort keys %{$buf{$tst}} ) {
			$title_uniq{$col} = 1;
		}
	}

	return (sort {$a cmp $b} keys %title_uniq);
}
#====================================================================
__END__

