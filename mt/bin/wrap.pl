#!/usr/bin/perl -w
#====================================================================
use strict;
use Getopt::Long;
#====================================================================
my $inputfile = "";
my $outputfile = "/dev/stdout";
my $type = "src"; 
#====================================================================
GetOptions(
	'in=s' => \$inputfile,
	'out=s'  => \$outputfile,
	'type=s' => \$type,
);
#====================================================================

if( $inputfile eq "" ) {
	print "ERROR: NO INPUT FILE\n";
	exit(0);	
}

my (@list_ref) = ();
if( $type eq "ref" ) {
	(@list_ref) = <$inputfile?>;
} else {
	(@list_ref) = ($inputfile);
}

if( $#list_ref < 0 ) {
	push(@list_ref, $inputfile);
}

# remove emty file
my (@list_file) = ();

for( my $i=0 ; $i<=$#list_ref ; $i++ ) {		
	my $size = -s $list_ref[$i];
	next if( !defined($size) || $size == 0 );
	
	my $line_cnt = `wc -l $list_ref[$i] | tr ' ' \\\\t | cut -f 1`;
	
	next if( $line_cnt == 0 );
	
	push(@list_file, $list_ref[$i]);
}

# read data
my (@buf) = ();
for( my $i=0 ; $i<=$#list_file ; $i++ ) {		
	unless( open(FILE_IN, "<".$list_file[$i]) ) {die "can not open ".$list_file[$i].": ".$!}

	while( my $line=<FILE_IN> ) {
		$line =~ s/^\s+|\s+$//g;
		
		# next if( $line eq "" );
		if( $line eq "" ) {
			push(@{$buf[$i]}, $line);
			next;
		}

		my (@token) = split(/\t/, $line);

		if( scalar(@token) == 1 ){
			push(@{$buf[$i]}, $line);
		} else {
			for( my $j=0 ; $j<scalar(@token) ; $j++ ) {
				push(@{$buf[$j]}, $token[$j]);
			}
		}		
	}

	close(FILE_IN);
}

# write data
unless( open(FILE_OUT, ">".$outputfile) ) {die "can not open ".$outputfile.": ".$!}

# print header
print FILE_OUT "<".$type."set setid=\"TEST-SET\" srclang=\"SRC_LANG\" trglang=\"TRG_LANG\">\n";

# print body
for( my $i=0 ; $i<scalar(@buf) ; $i++ ) {		
	printf FILE_OUT "<doc docid=\"TEST_DOC\" sysid=\"%d\">\n", $i;

	print $type, "\t", scalar(@{$buf[$i]}), "\n";
	for( my $j=0 ; $j<scalar(@{$buf[$i]}) ; $j++ ) {		
		printf FILE_OUT "<seg id=\"%d\"> %s </seg>\n", $j+1, $buf[$i][$j];
	}

	printf FILE_OUT "</doc>\n";
}

# print tail
print FILE_OUT "</".$type."set>\n";
	
close(FILE_OUT);
#====================================================================
__END__

