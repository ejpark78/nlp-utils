#!/usr/bin/perl
#====================================================================
use strict;
use Encode;
use FileHandle;
use File::Path;
use Getopt::Long;
use BerkeleyDB; 
#====================================================================
my (%args) = (
	"f" => "0",
);

GetOptions(
	"common" => \$args{"common"},
	"fn=s" => \$args{"fn"},
	"f=i" => \$args{"f"},
);
#====================================================================
# MAIN
#====================================================================
main: {
	binmode(STDIN, ":utf8");
	binmode(STDOUT, ":utf8");
	binmode(STDERR, ":utf8");

	my (%db);
	tie(%db, "BerkeleyDB::Btree", -Filename=>$args{"fn"}, -Flags=>DB_CREATE)
				or die("Cannot open ".$args{"fn"},": ".$!." ".$BerkeleyDB::Error."\n");

	my $cnt = 0;
	my $cnt_common = 0;
	while( my $line = <STDIN> ) {
		# printf STDERR "." if( $cnt++ % 1000 == 0 );
		# printf STDERR "(%s)\r", comma($cnt) if( $cnt % 100000 == 0 );

		#print "$line\n";
		$line =~ s/\s+$//;

		my (@t) = split(/\t/, $line);

		my $k = $t[$args{"f"}];

		$k = re_form($k);
		my $cnt = scalar(split(/\s+/, $k));

		$k =~ s/\s+$//g;	

		# print STDERR "[$k]\t$cnt\n";
		if( $cnt > 1 && $k ne "" && defined($db{$k}) ) {
			print STDERR "[$k]\t$line\n";
		} else {
			print "$line\n";
		}
	}

	# printf STDERR "(common : %s, total: %s)\n", comma($cnt_common), comma($cnt);

	untie(%db);
}
#====================================================================
# sub functions
#====================================================================
sub re_form {
	my $str = shift(@_);

	$str =~ s/[:;@,-~%"'?!(){}\[\]|=_$&*]/ /g;

	return $str;
}
#====================================================================
sub comma {
	my $cnt = shift(@_);

	$cnt = reverse join ",", (reverse $cnt) =~ /(\d{1,3})/g;

	return $cnt;
}
#====================================================================
#====================================================================
__END__

