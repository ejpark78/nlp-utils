perl -nle '
  (@t)  = split(/\t/, $_); 

  (@ta) = split(/\s+/, $t[2]); 
  (@tb) = split(/\s+/, $t[3]); 

  $ca = scalar(@ta);
  $cb = scalar(@tb);  

  $cdiff = abs($ca-$cb);

  print if( ($cdiff < $ca*2 && $cdiff < $cb*2) && ($ca < 50 && $cb < 50) )'
