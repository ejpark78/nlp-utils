#!/usr/bin/perl
#====================================================================
use strict;
use Encode;
use FileHandle;
use File::Path;
use Getopt::Long;
#====================================================================
my (%args) = (  
);

GetOptions(
  'diff_a' => \$args{"diff_a"},
  'common' => \$args{"common"},
  'bitext' => \$args{"bitext"},
  'f|fields=s' => \$args{"fields"},
);
#====================================================================
# MAIN
#====================================================================
main: {
  if( $args{"bitext"} ) {
    get_diff_column_bitext(\%args);  
  } else {
    get_diff_column(\%args);  
  }
}
#====================================================================
# sub functions
#====================================================================
sub get_diff_column_bitext {
  my (%param) = %{shift(@_)};

  binmode(STDIN, ":utf8");
  binmode(STDOUT, ":utf8");
  binmode(STDERR, ":utf8");

  my (@fields) = split(/,/, $param{"fields"});
  for( my $i=0 ; $i<scalar(@fields) ; $i++ ) {
    $fields[$i]--;
  }

  while( my $line = <STDIN> ) {
    $line =~ s/\s+$//;

    my (@token) = split(/\t/, $line);

    my $a = $token[$fields[0]];
    my $b = $token[$fields[1]];

    printf "%.4f\t%s\n", ($a-$b), $line;
  }
}
#====================================================================
sub get_diff_column {
  my (%param) = %{shift(@_)};

  binmode(STDIN, ":utf8");
  binmode(STDOUT, ":utf8");
  binmode(STDERR, ":utf8");

  my (@fields) = split(/,/, $param{"fields"});
  for( my $i=0 ; $i<scalar(@fields) ; $i++ ) {
    $fields[$i]--;
  }

  my (%idx_a, %buf_b) = ();

  while( my $line = <STDIN> ) {
    $line =~ s/\s+$//;

    my (@token) = split(/\t/, $line);

    my $a = $token[$fields[0]];
    my $b = $token[$fields[1]];

    $a = remove_stop_word($a);
    $b = remove_stop_word($b);

    $idx_a{$a} = 1 if( $a ne "" );

    push(@{$buf_b{$b}}, $line);
  }

  foreach my $b ( keys %buf_b ) {
    if( defined($idx_a{$b}) ) {
      if( $param{"common"} ) {
        print join("\n", @{$buf_b{$b}})."\n";
      }
      next;
    }

    print join("\n", @{$buf_b{$b}})."\n" if( !defined($param{"common"}) );
  }
}
#====================================================================
sub remove_stop_word {
  my $str = shift(@_);

  $str =~ s/\r?\n$//; 

  $str =~ s/\s+//g;
  $str =~ s/[\.|\?|\!|;|:|\<|\>|\[|\]|\{|\}|\-|\=|\+]//g;

  return $str;
}
#====================================================================
sub read_file {
  my $fn = shift(@_);
  my $ret = shift(@_);

  die "can not open : $fn $!\n" unless( open(FILE, $fn) );

  my $cnt = 0;
  foreach my $str ( <FILE> ) {
    # ($str) = split(/\t/, $str, 2);

    $str = remove_stop_word($str);
    next if( defined($ret->{$str}));
    next if( $str eq "" );

    # print STDERR "$str\n";
    $ret->{$str} = 1;

    $cnt++;
  } 

  # print STDERR "$cnt\n";
  
  close(FILE);
}
#====================================================================
__END__
