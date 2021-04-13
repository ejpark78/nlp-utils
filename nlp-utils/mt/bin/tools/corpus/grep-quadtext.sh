perl -nle '
  (@t)=split(/\t/, $_, 4); 
  print join("\t", @t) if( $t[2] !~ /^\s*$/ && $t[3] !~ /^\s*$/ );'
