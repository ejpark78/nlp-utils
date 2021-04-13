#!/usr/bin/perl
#====================================================================
use warnings;
use strict;
use utf8;
use Encode;
#====================================================================
binmode STDOUT, ":utf8";
binmode STDERR, ":utf8";
#====================================================================
main: {
	my (@wc, %uniq) = ();
	while( my $line = <STDIN> ) {
		$line =~ s/\s+$//;
		next if( $line eq "" || $line =~ /^#/ );

		push(@wc, scalar(split(/\s+/, $line)));

    $line = remove_stop_word($line);
    $uniq{$line}++;
	}

	printf "line count: %d, uniq count: %d, mean: %.2f, standard deviation: %.2f\n", scalar(@wc), scalar(keys %uniq), mean(@wc), standardDeviation(@wc, 0);
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
sub mean {  # 산술 평균 구하기
  return "NaN" if ($#_ < 0); # 빈 배열일 경우의 에러 처리

  my @array = @_;
  my $sum = 0.0;

  for (my $i = 0; $i <= $#array; $i++) {
    $sum += $array[$i];
  }

  # 소괄호로 둘러싸 주지 않으면
  # 연산자 우선 순위 때문에 버그 생김
  return $sum / ($#array + 1);
}
#====================================================================
sub standardDeviation {
  my $option = pop;
  my @array = @_;

  return "NaN" if ($#array + 1 < 2); # 배열 요소 개수가 최소한 2가 되어야 함

  my $sum = 0.0;
  my $sd = 0.0;
  my $diff;
  my $meanValue = mean(@array);

  for (my $i = 0; $i <= $#array; $i++) {
    $diff = $array[$i] - $meanValue;
    $sum += $diff * $diff;
  }
  $sd = sqrt($sum / ($#array + 1 - $option));

  return $sd;
}
#====================================================================
__END__