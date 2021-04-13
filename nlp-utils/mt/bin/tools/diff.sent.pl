#!/usr/bin/perl -w
#====================================================================
use strict ;
use utf8;

use Algorithm::Diff ;

use Getopt::Long;
#====================================================================
my (%args) = (
	start_tag_same => "<font>",
	start_tag_diff => "<font color=red>",

	end_tag_diff => "</font>",
	end_tag_same => "</font>",

	line_start => "<div>",
	line_end   => "</div>\n<br>\n",

	sep => "<br>",
	
	col => "1,2",
);
#--------------------------------------------------------------------
GetOptions(
	'show_tag' 	 	=> \$args{show_tag},
	'show_line_num' => \$args{show_line_num},
	'show_diff_only' => \$args{show_diff_only},
	'show_as_table' => \$args{show_as_table},

	'detail' 		=> \$args{detail},

	'token_space'   => \$args{token_space},

	'tag_a=s' => \$args{tag_a},
	'tag_b=s' => \$args{tag_b},
	'tag_c=s' => \$args{tag_c},

	'col=s' => \$args{col},
);
#====================================================================
binmode(STDIN, ":utf8");
binmode(STDOUT, ":utf8");
binmode(STDERR, ":utf8");
#====================================================================
#my (@seq_a) = qw/ I am a boy . /;
#my (@seq_b) = qw/ I am a student . /;

my ($idx_a, $idx_b) = split(/,/, $args{col});

$idx_a--;
$idx_b--;

my $line_num = 1;

while( <STDIN> ) {
	s/^\s+|\s+$//g;

	next if( $_ eq "" );

	my (@t) = split(/\t/, $_);

	my ($a, $b) = ($t[$idx_a], $t[$idx_b]);		

	next if( !defined($a) || !defined($b) );

	$a =~ s/\s+/ /g;
	$b =~ s/\s+/ /g;

	$a =~ s/^\s+|\s+$//g;
	$b =~ s/^\s+|\s+$//g;

	if( $args{token_space} ) {
		$a =~ s/ /_/g;
		$b =~ s/ /_/g;

		$a =~ s/(.)/ $1/g;
		$b =~ s/(.)/ $1/g;
	}

	my (@seq_a) = split(/ /, $a);
	my (@seq_b) = split(/ /, $b);

	my $diff = Algorithm::Diff->new( \@seq_a, \@seq_b );

	($a, $b) = ("", "");

	my $diff_log = "";

	my $flag_diff = 0;

	$diff->Base( 1 );
	while(  $diff->Next()  ) {
		# append start tag
		my $tag = $args{start_tag_diff};
		$tag = $args{start_tag_same} if( $diff->Same() );

		$a .= $tag;
		$b .= $tag;

		# get str 1
		my $buf_a = "";
		foreach( $diff->Items(1) ) {
			if( $args{token_space} ) {
				s/_/ /g;
				$buf_a .= $_;
			} else {
				$buf_a .= $_." ";
			}
		}

		# get str 2
		my $buf_b = "";
		foreach( $diff->Items(2) ) {
			if( $args{token_space} ) {
				s/_/ /g;
				$buf_b .= $_;
			} else {
				$buf_b .= $_." ";
			}
		}

		$a .= $buf_a;
		$b .= $buf_b;

		# append end tag
		if( $diff->Same() ) {
			$tag = $args{end_tag_same};
			$diff_log .= "<div><pre>SAME:\t".$buf_a."\t".$buf_b."</pre></div>\n";
		} else {
			$flag_diff = 1;

			$tag = $args{end_tag_diff};
			$diff_log .= "<div><pre>DIFF:\t".$buf_a."\t".$buf_b."</pre></div>\n";
		}

		$a .= $tag;
		$b .= $tag;
	}

	$t[$idx_a] = $a;
	$t[$idx_b] = $b;

	my $result = $args{line_start}.join($args{sep}, @t).$args{line_end}."\n";

	# make result	
	my ($col_a, $col_b, $col_c) = ("", "", "");
	
	$args{tag_a} = "A" if( !defined($args{tag_a}) );
	$args{tag_b} = "B" if( !defined($args{tag_b}) );
	$args{tag_c} = "C" if( !defined($args{tag_c}) );

	if( $args{show_tag} ) {
		my $span_line_num = "";
		$span_line_num = "<span>$line_num. </span>" if( $args{show_line_num} );
		
		$col_a = "<span>$args{tag_a}: </span>$a";
		$col_b = "<span>$args{tag_b}: </span>$b";

		$t[$idx_a] = $col_a;
		$t[$idx_b] = $col_b;

		$result = "$args{line_start}$col_c$args{sep}".join($args{sep}, @t)."$args{line_end}\n";
		
		if( $args{show_as_table} ) {
			my $width = "";
			$width = "width=".sprintf("%d", 100/scalar(@t))."%";
			
			$result  = "<tr>";
			
			foreach my $str ( @t ) {
				$result .= "<td border=1 $width>$str</td>";
			}
#			$result .= "  <td border=1 $width>$c</td>" if( $c ne "" );
#			$result .= "  <td border=1 $width>$a</td>";
#			$result .= "  <td border=1 $width>$b</td>";
			$result .= "</tr>";
		}
	}
	
	# print result
	if( $args{show_as_table} ) {
		print "<table border=1 width=100%>";
	}

	if( $args{show_diff_only} && $flag_diff ) {
		print $result;
		print $diff_log if( $args{detail} );
	} elsif( ! $args{show_diff_only} ) {
		print $result;
		print $diff_log if( $args{detail} );
	}

	if( $args{show_as_table} ) {
		print "</table>\n";
	}

	$line_num++;
}
#====================================================================
__END__
