#!/usr/bin/perl -w
#====================================================================
use strict;

use FindBin qw($Bin);
use Time::HiRes;
use Getopt::Long;
use HTML::TokeParser;
use IPC::Open3;
#use Date::Format;

use POSIX;
use Term::ANSIColor qw(:constants);

use Data::Uniqid qw ( suniqid uniqid );

use lib "$Bin";

require "align.pm";
#====================================================================
my (%args) = ();

GetOptions(
	# run option
	'batch_cnn_bitext' => \$args{batch_cnn_bitext},
	'batch_donga_bitext' => \$args{batch_donga_bitext},

	'merge_test' => \$args{merge_test},
	'merge_bitext' => \$args{merge_bitext},
	'merge_cnn_bitext' => \$args{merge_cnn_bitext},
	'merge_donga_bitext' => \$args{merge_donga_bitext},

	'extract_smi' => \$args{extract_smi},

	'remove_dup_line' => \$args{remove_dup_line},

	'a=s' => \$args{a},
	'b=s' => \$args{b},
	'align_info=s' => \$args{align_info},

	'get_page' => \$args{get_page},
	'get_link' => \$args{get_link},

	'extract_tag'  => \$args{extract_tag},
	'extract_text' => \$args{extract_text},

	'text2dbCNN' => \$args{text2dbCNN},
	'text2dbSMI' => \$args{text2dbSMI},

	'text2db' => \$args{text2db},
	'text2dbBitext' => \$args{text2dbBitext},
	'set_primary' => \$args{set_primary},

	'dry' => \$args{dry},
	
	'path=s' => \$args{path},
	'url_list=s' => \$args{url_list},
	'remove_line=s' => \$args{remove_line},
	
	'fn=s' => \$args{fn},
	'table_name=s' => \$args{table_name},
	'col_list=s' => \$args{col_list},
	'fn_url_db=s' => \$args{fn_url_db},

	'test' => \$args{test},
	'tag2text' => \$args{tag2text},
	
	'set_uniq' => \$args{set_uniq},	
	
	'use_fts3' => \$args{use_fts3},

	'sleep=i' => \$args{sleep},

);
#====================================================================
main: {
	binmode(STDIN, ":utf8");
	binmode(STDOUT, ":utf8");
	binmode(STDERR, ":utf8");

	if( $args{test} ) {
		foreach my $c ( <STDIN> ) {
#			$c =~ s/(.)/$1/g;

#			$c =~ s/\x91|\x92/\'/g;
			$c =~ s/\x93|\x94/\"/g;
			$c =~ s/\x91|\x92/\'/g;
			
			print $c;				
#			foreach my $w ( split(/\t/, $c) ) {
#				print $w, "\t", sprintf("%x", ord($w)), "\t", chr(0x92), "\n";				
#			}
		
		}
		
		exit(1);	
	}

	batchCnnBitext()	if( $args{batch_cnn_bitext} );
	batchDongaBitext()	if( $args{batch_donga_bitext} );

	mergeTest()			if( $args{merge_test} );
	mergeBitext()		if( $args{merge_bitext} ); 
	mergeCnnBitext()	if( $args{merge_cnn_bitext} );
	mergeDongaBitext() 	if( $args{merge_donga_bitext} );

	removeLine()		if( $args{remove_line} );
	removeDupLine()		if( $args{remove_dup_line} );

	extractSMI() 		if( $args{extract_smi} );
	extractLink()		if( $args{extract_tag} );
	extractText()		if( $args{extract_text} );

	getPage()			if( $args{get_page} );

	text2dbCNN("bitext.db", "cnn")	if( $args{text2dbCNN} );	
	text2dbSMI("bitext.db", "smi")	if( $args{text2dbSMI} );
	text2dbBitext(\%args) if( $args{text2dbBitext} || $args{text2db} );
	
	tag2text() if( $args{tag2text} );
}
#====================================================================
sub readSmiFile {
	my ($_fn, $_encoding) = @_;

    my (@ret) = ();

	my $open_mode = "<";
	$open_mode = "<:gzip" if( $_fn =~ /\.gz$/ );

	if( defined($_encoding) && $_encoding ne "" ) {
		$open_mode = "<:encoding($_encoding)";
	} else {
		my $charset = `grep lang: $_fn`;

		if( $charset =~ /lang:(.+?);/ ) {
			my $lang = $1;
			if( $lang =~ /^(ko|kr|en|us|fr|eg)-/i || $lang =~ /korean/i ) {
				$open_mode = "<:encoding(euc-kr)";
			} else {
				print STDERR "# readSmiFile \n";
			}
		}

		print STDERR "# charset: $charset\n";
	}

	print STDERR "# Open Mode: $open_mode\n";

	return () unless( open(FILE, $open_mode, $_fn) );

	binmode(FILE, ":utf8");

	no warnings;

	push(@ret, <FILE>);

	use warnings;

	close(FILE);

	return (@ret);
}
#====================================================================
sub extractSMI {
	use utf8;
	
	foreach my $fn ( @ARGV ) {
		print "## $fn\n";
		print STDERR "## $fn\n";

		my (@html) = readSmiFile($fn, "euc-kr");

		my $str = join("", @html);

		$str =~ s/\r\n//g;
		$str =~ s/\n//g;
		$str =~ s/&\#(\d+?);/chr($1)/eg;
		
		my (%data) = ();
		
		$str =~ s/&nbsp;/\n/ig;

		# <SYNC Start=55736><P Class=KRCC>꺼내야 합니다.<SYNC Start=57374><P Class=KRCC>
		# <SYNC Start=(\d+)><P Class=(\w+)>(.+?)<SYNC Start=\d+><P Class=(\w+)>
		foreach my $str ( split(/\n/, $str) ) {
			my ($st, $lang, $line, $en) = ($str =~ m/<SYNC Start=(\d+)><P Class=(\w+)>(.+?)<SYNC Start=(\d+)>/i );
			next if( !defined($st) || !defined($en) || !defined($lang) || !defined($line) );
			
			$line =~ s/<br>/ /ig;

			$data{sprintf("%010d-%010d", $st, $en)}{$lang} = $line;
		}
		
		(%data) = printSmiAligned(%data);
		(%data) = printSmiAligned(%data);
		(%data) = printSmiAligned(%data);
		
		if( scalar(keys %data) > 0 ) {
			print STDERR "ERROR Aligned Text: ", scalar(keys %data), "\n";
		}
	}
}
#====================================================================
sub printSmiAligned {
	my (%data) = @_;
	
	my (%data2) = ();
	foreach my $time ( sort keys %data ) {
		my (@data_key) = (sort keys %{$data{$time}});

		my $buf = "";
		foreach my $key ( @data_key ) {			
			$buf .= "<$key>$data{$time}{$key}</$key>\t";
		}
		
		next if( $buf eq "" );

		if( scalar(@data_key) < 2 ) {
			foreach my $key ( @data_key ) {
				my ($a, $b) = split(/-/, $time, 2);
				
				$a =~ s/.$//;
				$b =~ s/.$//;
				
				$data2{"$a-$b"}{$key} = $data{$time}{$key};
			}
		} else {
			print "$time\t$buf\n";
		}
	}
	
	return (%data2);
}
#====================================================================
sub removeDupLine {
	my $a = $args{a};
	my $b = $args{b};

	my (%list_b) = ();

	foreach my $line ( readFile($b) ) {
		$list_b{$line} = 1;
	}

#	print STDERR $a, ":", scalar(keys %list_b), "\n";
#	print STDERR $b, ":", scalar(readFile($b));

	foreach my $line ( readFile($a) ) {
		next if( defined($list_b{$line}) );

		print $line."\n";
	}
}
#====================================================================
sub readFile {
	my ($_fn) = (@_);

	my $file;

	my ($open_mode) = ("<");
	$open_mode = "<:gzip" if( $_fn =~ /\.gz$/ );
	die "$_fn\n" unless( open($file, $open_mode, $_fn) );

	binmode($file, ":utf8");

	my (@text) = ();
	foreach my $line ( <$file> ) {
		$line =~ s/^\s+|\s+$//g;

		last if( $line eq "#__END__" );
		next if( $line =~ /^#/ || $line eq "" );

		push(@text, $line);
	}

	close($file);

	return (@text);
}
#====================================================================
sub batchDongaBitext {
#	my $fn_header 	= strftime('%Y-%m-%d', localtime);
	my $fn_header 	= strftime('%Y-%m-%d_%H.%M.%S', localtime);
	my $wget 		= "$Bin/wget.pl";
	my $path 		= ( -e $args{path}     ) ? $args{path} : "/home/ejpark/corpus/bitext/donga";
	my $url_list	= ( -e $args{url_list} ) ? $args{url_list}  : "/home/ejpark/corpus/bitext/donga/url_list_daily";
	my $pl 			= "perl -nle";

#	$fn_header = "2010-05-13_16.31.43";

	my $_dry 		= ( $args{dry} ) ? 1 : 0;

	my $tmp = $path."/tmp";

	mkdir($tmp) if( !-e $tmp );

	my $cmd;

	print BOLD, BLUE, "\n## wget page list.\n", RESET;
	$cmd = "cat $url_list | $wget -get_page > $tmp/$fn_header.page_list_en_daily";
	safeSystem($cmd, $_dry);

	print BOLD, BLUE, "\n## update downloaded url list\n", RESET;
	$cmd = "zcat $path/page_en.*.gz | ".
	 			"$pl '(\$a)=split(/<!--NEW_LINE-->/,\$_,2);\$a=~s/^.+URL: | -->\$//g;print \$a' | ".
	 			"sort -u > $tmp/$fn_header.dn_list";
	safeSystem($cmd, $_dry);

	print BOLD, BLUE, "\n## extract eng. list\n", RESET;
	$cmd  = "cat $tmp/$fn_header.page_list_en_daily | $wget -extract_tag | cut -f2- | sort | uniq -c | ";
	$cmd .= "$pl 's/^\\s+|\\s+\$//g; (\$a, \$b) = split(/\\s+/, \$_); print \$b if \$a == 1 || \$a == 2 ' | ".
				"grep -v ^# | grep biid | sort -u > $tmp/$fn_header.url_list_en_daily";
	safeSystem($cmd, $_dry);

	print BOLD, BLUE, "\n## remove dup. url\n", RESET;
	$cmd  = "wget.pl -remove_dup_line -a $tmp/$fn_header.url_list_en_daily -b $tmp/$fn_header.dn_list | sort -u > a ; mv a $tmp/$fn_header.new_url";
	safeSystem($cmd, $_dry);

	if( !$_dry && `wc -l $tmp/$fn_header.new_url | cut -d' ' -f1` < 10 ) {
		print BOLD, BLUE, "\n## clear tmp file\n", RESET;
		$cmd = "rm $tmp/$fn_header.*";
		safeSystem($cmd, $_dry);

		return;
	}

	print BOLD, BLUE, "\n## wget eng. page\n", RESET;
	$cmd = "cat $tmp/$fn_header.new_url | $wget -get_page >> $tmp/$fn_header.page_en";
	safeSystem($cmd, $_dry);

	use utf8;

	print BOLD, BLUE, "\n## extract kor. page (1)\n", RESET;
	$cmd = "cat $tmp/$fn_header.page_en | $wget -extract_tag | ".
				"grep 'k2srv' | sort -u | cut -f1,2 > $tmp/$fn_header.align_info_enkr";
	safeSystem($cmd, $_dry);

	print BOLD, BLUE, "\n## extract kor. page (2)\n", RESET;
	$cmd = "cut -f2 $tmp/$fn_header.align_info_enkr > $tmp/$fn_header.url_kr";
	safeSystem($cmd, $_dry);

	print BOLD, BLUE, "\n## wget kor. page\n", RESET;
	$cmd = "cat $tmp/$fn_header.url_kr | $wget -get_page >> $tmp/$fn_header.page_kr";
	safeSystem($cmd, $_dry);

	print BOLD, BLUE, "\n## move to data dir.\n", RESET;
	$cmd = "gzip $tmp/$fn_header.page_kr $tmp/$fn_header.page_en";
	safeSystem($cmd, $_dry);

	$cmd = "mv $tmp/$fn_header.page_kr.gz $path/page_kr.$fn_header.gz ; mv $tmp/$fn_header.page_en.gz $path/page_en.$fn_header.gz";
	safeSystem($cmd, $_dry);

	print BOLD, BLUE, "\n## extract text\n", RESET;
	$cmd = "zcat $path/page_en.$fn_header.gz | wget.pl -extract_text | gzip > $path/text_en.$fn_header.gz";
	safeSystem($cmd, $_dry);

	$cmd = "zcat $path/page_kr.$fn_header.gz | wget.pl -extract_text | gzip > $path/text_kr.$fn_header.gz";
	safeSystem($cmd, $_dry);

	print BOLD, BLUE, "\n## trim text\n", RESET;
	$cmd = "zcat $path/text_kr.$fn_header.gz | cut -f3- | sort | uniq -c | $pl 's/^\\s+//;(\$a,\$b)=split(/ /,\$_,2);print \$b if \$a > 10' | sort -u > $tmp/$fn_header.stop_line_kr";
	safeSystem($cmd, $_dry);

	$cmd = "zcat $path/text_en.$fn_header.gz | cut -f3- | sort | uniq -c | $pl 's/^\\s+//;(\$a,\$b)=split(/ /,\$_,2);print \$b if \$a > 10' | sort -u > $tmp/$fn_header.stop_line_en";
	safeSystem($cmd, $_dry);

	$cmd = "zcat $path/text_kr.$fn_header.gz | wget.pl -remove_line $tmp/$fn_header.stop_line_kr | gzip > $path/text_kr_trimed.$fn_header.gz";
	safeSystem($cmd, $_dry);

	$cmd = "zcat $path/text_en.$fn_header.gz | wget.pl -remove_line $tmp/$fn_header.stop_line_en | gzip > $path/text_en_trimed.$fn_header.gz";
	safeSystem($cmd, $_dry);

	print BOLD, BLUE, "\n## merge\n", RESET;
	$cmd = "$wget -merge_donga_bitext -align_info $tmp/$fn_header.align_info_enkr -a $path/text_en_trimed.$fn_header.gz -b $path/text_kr_trimed.$fn_header.gz | gzip > $path/en-kr.$fn_header.gz";
	safeSystem($cmd, $_dry);

	print BOLD, BLUE, "\n## clear tmp file\n", RESET;
	$cmd = "rm $tmp/$fn_header.*";
	safeSystem($cmd, $_dry);
}
#====================================================================
sub batchCnnBitext {
	my $fn_header 	= strftime('%Y-%m-%d_%H.%M.%S', localtime);
	my $wget 		= "$Bin/wget.pl";
	my $path 		= ( -e $args{path}     ) ? $args{path} : "/home/ejpark/corpus/bitext/cnn";
	my $url_list	= ( -e $args{url_list} ) ? $args{url_list}  : "/home/ejpark/corpus/bitext/cnn/url_list_daily";
	my $pl 			= "perl -nle";

#	$fn_header = "2010-05-06_16.34.04";

	my $_dry 		= ( $args{dry} ) ? 1 : 0;

	my $tmp = $path."/tmp";

	mkdir($tmp) if( !-e $tmp );

	my $cmd;

	print BOLD, BLUE, "\n## wget page list.\n", RESET;
	$cmd = "cat $url_list | $wget -get_page > $tmp/$fn_header.page_list_en_daily";
	safeSystem($cmd, $_dry);

	print BOLD, BLUE, "\n## update downloaded url list\n", RESET;
	$cmd = "zcat $path/page_en.*.gz | ".
	 			"$pl '(\$a)=split(/<!--NEW_LINE-->/,\$_,2);\$a=~s/^.+URL: | -->\$//g;print \$a' | ".
	 			"sort -u > $tmp/$fn_header.dn_list";
	safeSystem($cmd, $_dry);

	print BOLD, BLUE, "\n## extract eng. list\n", RESET;
	$cmd  = "cat $tmp/$fn_header.page_list_en_daily | $wget -extract_tag | cut -f2- | sort | uniq -c | ";
	$cmd .= "$pl 's/^\\s+|\\s+\$//g; (\$a, \$b) = split(/\\s+/, \$_); print \$b if \$a == 1 || \$a == 2 ' | ".
				"grep -v ^# | grep -v list | sort -u > $tmp/$fn_header.url_list_en_daily";
	safeSystem($cmd, $_dry);

	print BOLD, BLUE, "\n## remove dup. url\n", RESET;
	$cmd  = "wget.pl -remove_dup_line -a $tmp/$fn_header.url_list_en_daily -b $tmp/$fn_header.dn_list | sort -u > a ; mv a $tmp/$fn_header.new_url";
	safeSystem($cmd, $_dry);

	if( !$_dry && `wc -l $tmp/$fn_header.new_url | cut -d' ' -f1` < 10 ) {
		print BOLD, BLUE, "\n## clear tmp file\n", RESET;
		$cmd = "rm $tmp/$fn_header.*";
		safeSystem($cmd, $_dry);

		return;
	}

	print BOLD, BLUE, "\n## wget eng. page\n", RESET;
	$cmd = "cat $tmp/$fn_header.new_url | $wget -get_page >> $tmp/$fn_header.page_en";
	safeSystem($cmd, $_dry);

	use utf8;

	print BOLD, BLUE, "\n## extract kor. page (1)\n", RESET;
	$cmd = "cat $tmp/$fn_header.page_en | $wget -extract_tag | ".
				"grep '한글기사보기' | sort -u | cut -f1,2 > $tmp/$fn_header.align_info_enkr";
	safeSystem($cmd, $_dry);

	print BOLD, BLUE, "\n## extract kor. page (2)\n", RESET;
	$cmd = "cut -f2 $tmp/$fn_header.align_info_enkr > $tmp/$fn_header.url_kr";
	safeSystem($cmd, $_dry);

	print BOLD, BLUE, "\n## wget kor. page\n", RESET;
	$cmd = "cat $tmp/$fn_header.url_kr | $wget -get_page >> $tmp/$fn_header.page_kr";
	safeSystem($cmd, $_dry);

	print BOLD, BLUE, "\n## move to data dir.\n", RESET;
	$cmd = "gzip $tmp/$fn_header.page_kr $tmp/$fn_header.page_en";
	safeSystem($cmd, $_dry);

	$cmd = "mv $tmp/$fn_header.page_kr.gz $path/page_kr.$fn_header.gz ; mv $tmp/$fn_header.page_en.gz $path/page_en.$fn_header.gz";
	safeSystem($cmd, $_dry);

	print BOLD, BLUE, "\n## extract text\n", RESET;
	$cmd = "zcat $path/page_en.$fn_header.gz | wget.pl -extract_text | gzip > $path/text_en.$fn_header.gz";
	safeSystem($cmd, $_dry);

	$cmd = "zcat $path/page_kr.$fn_header.gz | wget.pl -extract_text | gzip > $path/text_kr.$fn_header.gz";
	safeSystem($cmd, $_dry);

	print BOLD, BLUE, "\n## trim text\n", RESET;
	$cmd = "zcat $path/text_kr.$fn_header.gz | cut -f3- | sort | uniq -c | $pl 's/^\\s+//;(\$a,\$b)=split(/ /,\$_,2);print \$b if \$a > 10' | sort -u > $tmp/$fn_header.stop_line_kr";
	safeSystem($cmd, $_dry);

	$cmd = "zcat $path/text_en.$fn_header.gz | cut -f3- | sort | uniq -c | $pl 's/^\\s+//;(\$a,\$b)=split(/ /,\$_,2);print \$b if \$a > 10' | sort -u > $tmp/$fn_header.stop_line_en";
	safeSystem($cmd, $_dry);

	$cmd = "zcat $path/text_kr.$fn_header.gz | wget.pl -remove_line $tmp/$fn_header.stop_line_kr | grep -v \"\\<dl\\>\" | gzip > $path/text_kr_trimed.$fn_header.gz";
	safeSystem($cmd, $_dry);

	$cmd = "zcat $path/text_en.$fn_header.gz | wget.pl -remove_line $tmp/$fn_header.stop_line_en | grep -v \"\\<dl\\>\" | gzip > $path/text_en_trimed.$fn_header.gz";
	safeSystem($cmd, $_dry);

	print BOLD, BLUE, "\n## merge\n", RESET;
	$cmd = "$wget -merge_cnn_bitext -align_info $tmp/$fn_header.align_info_enkr -a $path/text_en_trimed.$fn_header.gz -b $path/text_kr_trimed.$fn_header.gz | gzip > $path/cnn_en-kr.$fn_header.gz";
	safeSystem($cmd, $_dry);

	print BOLD, BLUE, "\n## clear tmp file\n", RESET;
	$cmd = "rm $tmp/$fn_header.*";
	safeSystem($cmd, $_dry);
}
#====================================================================
sub safeSystem {
	my ($_cmd, $_dry) = @_;

	if( $_dry ) {
		print $_cmd."\n";
		return;
	}

	print STDERR RESET, "# Executing: $_cmd\n";

	system($_cmd);

	if( $? == -1 ) {
		print STDERR "# Failed to execute: @_\n  $!\n";
		exit(1);
	} elsif( $? & 127 ) {
		printf STDERR "# Execution of: @_\n  died with signal %d, %s coredump\n", ($? & 127),  ($? & 128) ? 'with' : 'without';
		exit(1);
	} else {
		my $exitcode = $? >> 8;
		print STDERR "# Exit code: $exitcode\n" if $exitcode;
		return ! $exitcode;
	}

	print STDERR "\n";
}
#====================================================================
sub text2dbSMI {
	use DBI;

	my ($_db_name, $_table_name) = @_;

    my $dbh = DBI->connect("dbi:SQLite:dbname=$_db_name","","",{AutoCommit => 1, PrintError => 1});

	# Maximise compatibility
	$dbh->do('PRAGMA legacy_file_format = 1');

	# Turn on all the go-faster pragmas
	$dbh->do('PRAGMA synchronous  = 0');
	$dbh->do('PRAGMA temp_store   = 2');
	$dbh->do('PRAGMA journal_mode = OFF');
	$dbh->do('PRAGMA locking_mode = EXCLUSIVE');

	my $query = "CREATE TABLE IF NOT EXISTS $_table_name (speech_time INTEGER, a VARCHAR(255), b VARCHAR(255))";
	$dbh->do($query);

	my $cnt = 0;
	foreach( <STDIN> ) {
		s/^\s+|\s+$//g;

		next if $_ eq "";

		my ($page, $eng, $kor) = split(/\t/, $_, 3);

		if( !defined($kor) ) {
#			print $_."\n";
			next;
		}

#		print "\r($page)";

		$eng =~ s!^<([^>]+)>(.+)</\\1>$!$2!g;
		$kor =~ s!^<([^>]+)>(.+)</\\1>$!$2!g;

		$eng =~ s/\'/\'\'/g;
		$kor =~ s/\'/\'\'/g;

		$query = "INSERT INTO $_table_name VALUES ('$page', '$eng', '$kor')";
	    $dbh->do($query);

		print STDERR "\r".$cnt if( ($cnt++ % 1000) == 0 );
	}

    $dbh->disconnect();
}
#====================================================================
sub text2dbCNN {
	use DBI;

	my ($_db_name, $_table_name) = @_;

    my $dbh = DBI->connect("dbi:SQLite:dbname=$_db_name","","",{AutoCommit => 1, PrintError => 1});

	# Maximise compatibility
	$dbh->do('PRAGMA legacy_file_format = 1');

	# Turn on all the go-faster pragmas
	$dbh->do('PRAGMA synchronous  = 0');
	$dbh->do('PRAGMA temp_store   = 2');
	$dbh->do('PRAGMA journal_mode = OFF');
	$dbh->do('PRAGMA locking_mode = EXCLUSIVE');

	my $query = "CREATE TABLE IF NOT EXISTS $_table_name (page INTEGER, eng VARCHAR(255), kor VARCHAR(255))";
	$dbh->do($query);

	my $cnt = 0;
	foreach( <STDIN> ) {
		s/^\s+|\s+$//g;

		next if $_ eq "";

		my ($page, $eng, $kor) = split(/\t/, $_, 3);

		if( !defined($kor) ) {
#			print $_."\n";
			next;
		}

#		print "\r($page)";

		$eng =~ s/\'/\'\'/g;
		$kor =~ s/\'/\'\'/g;

		$query = "INSERT INTO $_table_name VALUES ($page, '$eng', '$kor')";
	    $dbh->do($query);

		print STDERR "\r".$cnt if( ($cnt++ % 1000) == 0 );
	}

    $dbh->disconnect();
}
#====================================================================
sub text2dbBitext 
{
	# sudo apt-get install libicu42
	
	use DBI;
	
	no warnings "all";

	my ($_args) = @_;
	
	my $_db_name 	= $_args->{fn};
	my $_table_name = $_args->{table_name};
	my $_tbl_list 	= $_args->{col_list};
	my $_set_primary = $_args->{set_primary};
	my $_set_uniq    = $_args->{set_uniq};
	
	my $_use_fts = $_args->{use_fts3};
		
	# token tbl_list
	# ex) src,trg   or src:s,trg:s,page:i
	$_tbl_list = "src,trg" if( !defined($_tbl_list) || $_tbl_list eq "" );
	
	my (@tbl_list) = split(/,/, $_tbl_list);

	# connect db
    my $dbh = DBI->connect("dbi:SQLite:dbname=$_db_name","","",{AutoCommit => 1, PrintError => 1});

	# Maximise compatibility
	$dbh->do('PRAGMA legacy_file_format = 1');

	# Turn on all the go-faster pragmas
	$dbh->do('PRAGMA synchronous  = 0');
	$dbh->do('PRAGMA temp_store   = 2');
	$dbh->do('PRAGMA journal_mode = OFF');
	$dbh->do('PRAGMA locking_mode = EXCLUSIVE');

	my (@col_list) = ();
	foreach my $col ( @tbl_list ) {
		if( $col eq "m_date" ) {
			push(@col_list, "$col DATE DEFAULT (datetime('now','localtime'))");
		} else {
			push(@col_list, "$col TEXT");
		}
	}

	my $primary_key = "";
	$primary_key    = ", PRIMARY KEY (".join(",", @tbl_list).")" if( defined($_set_primary) );
	
	my $uniq_key = "";
	$uniq_key    = ", UNIQUE (".join(",", @tbl_list).")" if( defined($_set_uniq) && !defined($_set_primary) );
	

	my $query = "CREATE TABLE IF NOT EXISTS $_table_name (".join(",", @col_list)." $primary_key $uniq_key)";	
	$query    = "CREATE VIRTUAL TABLE $_table_name USING fts3 (".join(",", @col_list)." $primary_key $uniq_key)" if( defined($_use_fts) );
	
	print STDERR "query: $query\n";
	$dbh->do($query);
	
#	return;

	my $cnt = 0;
	foreach( <STDIN> ) {
#		s/^\s+|\s+$//g;
		s/\r?\n$//;

		next if $_ eq "";

		my (@cols) = split(/\t/, $_, scalar(@tbl_list));

		if( scalar(@cols) != scalar(@tbl_list) ) {
			print STDERR "Mismatch column count: $_\n";
			next;
		}
		
		for( my $i=0 ; $i<scalar(@cols) ; $i++ ) {
			if( $cols[$i] =~ /datetime/ ) {
				$cols[$i] = $cols[$i];
			} else {
				$cols[$i] =~ s/\'/\'\'/g;			
				$cols[$i] = "'".$cols[$i]."'";
			}
		}

		$query = "INSERT INTO $_table_name (".join(",", @tbl_list).") VALUES (".join(",",@cols).")";
#		print STDERR "query: $query\n";
	    $dbh->do($query);

		print STDERR "\r".$cnt if( ($cnt++ % 1000) == 0 );
	}

    $dbh->disconnect();
}
#====================================================================
sub mergeTest {
	my $a = $args{a};
	my $b = $args{b};
	my $c = $args{align_info};

	my (%align) = readAlignInfo($c);

	my (%text_a) = readTextFile($a);
	my (%text_b) = readTextFile($b);

	foreach my $k ( keys %text_a ) {
		if( !defined($text_b{$align{$k}}) ) {
			print STDERR "# ERROR ALIGN: $k\n";
			next;
		}

		print "\n======================================================================\n";

		my (@list_a) = split(/\n/, $text_a{$k});
		my (@list_b) = split(/\n/, $text_b{$align{$k}});

#		if( scalar(@list_a) == scalar(@list_b) ) {
#			my $max = (scalar(@list_a)>scalar(@list_b))?scalar(@list_a):scalar(@list_b);
#
#			for( my $i=0 ; $i<$max ; $i++ ) {
#				my $str_a = (defined($list_a[$i]))?$list_a[$i]:"NULL";
#				my $str_b = (defined($list_b[$i]))?$list_b[$i]:"NULL";
#
#				last if( $str_a =~ /\p{Hangul}/ );
#				last if( $str_b !~ /\p{Hangul}/ );
#
#				print "$k\t$str_a\t$str_b\n";
#			}
#		} else {
			print "## $k\n";
			print join("\n", @list_a),"\n\n";
			print "## $align{$k}\n";
			print join("\n", @list_b),"\n\n";
#		}

		print "\n======================================================================\n";
	}
}
#====================================================================
sub mergeBitext {
	my $a = $args{a};
	my $b = $args{b};
	my $c = $args{align_info};

	my (%align) = readAlignInfo($c);

	my (%text_a) = readTextFile($a);
	my (%text_b) = readTextFile($b);

	foreach my $k ( keys %text_a ) {
		if( !defined($align{$k}) || !defined($text_b{$align{$k}}) ) {
			print STDERR "# ERROR ALIGN: $k\n";
			next;
		}

		my (@list_a) = split(/\n/, $text_a{$k});
		my (@list_b) = split(/\n/, $text_b{$align{$k}});

		my $max = (scalar(@list_a)>scalar(@list_b))?scalar(@list_a):scalar(@list_b);

		for( my $i=0 ; $i<$max ; $i++ ) {
			my $str_a = (defined($list_a[$i]))?$list_a[$i]:"NULL";
			my $str_b = (defined($list_b[$i]))?$list_b[$i]:"NULL";

			print "$k\t$str_a\t$str_b\n";
		}

		print "\n\n";
	}
}
#====================================================================
sub mergeDongaBitext {
	my $a = $args{a};
	my $b = $args{b};
	my $c = $args{align_info};
	
	my $_acronym_dict 	= "$Bin/acronym.dict";
	my $_roman_dict 	= "$Bin/dict.kren.roman.utf8";
	
	binmode(STDIN, ":utf8");
	binmode(STDOUT, ":utf8");
	binmode(STDERR, ":utf8");

	my (@_abbr) = ();
	$_abbr[0] = "P[hH](\\\.)?D|M([rs]|rs|me)|Dr|U\\\.S(\\\.A|)|[aApP]\\\.[mM]|Calif|Fla|D\\\.C|N\\\.Y|Ont|Pa|V[Aa]|[MS][Tt]|Jan|Feb|Mar|Apr|Aug|Sept?|Oct|Nov|Dec|Assoc|[oO]\\\.[kK]|Co|R\\\.V|Gov|Se[nc]|U\\\.N|\[A-Z\]|i\\\.e|e\\\.g|vs?|Re[pv]|Gen|Univ|Jr|[fF]t|[Ss]gt|[Pp]res|[Pp]rof|[Aa]pprox|[Cc]orp|[Dd]ef";
	$_abbr[1] = "D\\\.C";
	$_abbr[2] = LoadDictionaryAcronym($_acronym_dict);
	
#	my (%dict_kren, %dict_roman) = ();
#	ReadDict("dict.noun.all.utf8.gz", \%dict_kren);
#	ReadDictRoman($_roman_dict, \%dict_roman);

	my (%align) = readAlignInfo($c);

	my (%text_a) = readTextFile($a);
	my (%text_b) = readTextFile($b);
	
	my $cnt = 10;
	
	print STDERR "Text A:", scalar( keys %text_a ), "\n";
	print STDERR "Text B:", scalar( keys %text_b ), "\n";

	foreach my $k ( keys %text_a ) {
		if( !defined($align{$k}) || !defined($text_b{$align{$k}}) ) {
#			print STDERR "# ERROR ALIGN: $k\n";
			next;
		}
		
#		print "$text_a{$k}\n$text_b{$align{$k}}\n";
		
		my (@list_a) = trimDonga( split(/\n/, $text_a{$k}) );
		my (@list_b) = trimDonga( split(/\n/, $text_b{$align{$k}}) );
		
		my (@sent_list_en, @sent_list_kr) = ();
		
		foreach my $line ( @list_a ) {push(@sent_list_en, TokenSentenceEnglish($line, $_abbr[0], $_abbr[1], $_abbr[2]))}		
		foreach my $line ( @list_b ) {push(@sent_list_kr, TokenSentenceKorean($line))}
		
		my ($a, $b, @th_list) = splitSentanceByLength(\@sent_list_en, \@sent_list_kr);
		
		(@list_a) = (@{$a});
		(@list_b) = (@{$b});
		
#		next if( scalar(@list_a) == scalar(@list_b) );
		
		my $max = ( scalar(@list_a)>scalar(@list_b) ) ? scalar(@list_a) : scalar(@list_b);

		$k =~ s/^.+biid=(\d+)//;
		$k = $1 if( defined($1) );
		
		my $tag = "DIFF";
		$tag = "SAME" if( scalar(@list_a) == scalar(@list_b) );

		for( my $i=0 ; $i<$max ; $i++ ) {
			my $str_a = ( defined($list_a[$i]) ) ? $list_a[$i] : "";
			my $str_b = ( defined($list_b[$i]) ) ? $list_b[$i] : "";
			
			next if( $str_a eq "" && $str_b eq "" );

			$th_list[$i] = "" if( !defined($th_list[$i]) );
						
			$str_a = "NULL" if( $str_a eq "" );
			$str_b = "NULL" if( $str_b eq "" );
			
			
			print "$tag-$k\t$str_a\t$str_b\n\n";

#			print "$th_list[$i]:\n$str_a\n$str_b\n\n";

		}
	}
}
#====================================================================
sub splitSentanceByLength {
	my ($_a, $_b) = (@_);

	my (@t_a) = removeEmptyLine(@{$_a});
	my (@t_b) = removeEmptyLine(@{$_b});

	my ($len_a, $len_b) = (length(join(" ", @t_a)), length(join(" ", @t_b)));
	
	my ($max, $min) = ( scalar(@t_a)>scalar(@t_b) ) ? (scalar(@t_a), scalar(@t_b)) : (scalar(@t_b), scalar(@t_a));

#	print "(len_a, len_b) = ($len_a, $len_b) ", $len_a - $len_b, " ", $len_a/$min, " ", $len_b/$min," \n";
	
	my (@th_list) = ();
	
	my $limit = 5;
	
	# check length
	for( my $i=0 ; $i<$max ; $i++ ) {
		$t_a[$i] = "" if( !defined($t_a[$i]) );
		$t_b[$i] = "" if( !defined($t_b[$i]) );
		
		next if( $t_a[$i] eq "" && $t_b[$i] eq "" );
		
		my $th = computTH($t_a[$i], $t_b[$i], $len_a, $len_b);

		if( abs($th) > $limit ) {
			# merge b
			if( $th > 0 && defined($t_b[$i+1]) ) {	
				 my $th_b = computTH($t_a[$i], $t_b[$i]." ".$t_b[$i+1], $len_a, $len_b);

				 if( abs($th_b) < $limit ) {
				 	 (@t_b) = mergeSentance(\@t_b, $i, $i+1);
				 	 $th = computTH($t_a[$i], $t_b[$i], $len_a, $len_b);
				 } elsif( $th_b > 0 ) {
				 	 (@t_b) = mergeSentance(\@t_b, $i, $i+1);
				 	 $th = computTH($t_a[$i], $t_b[$i], $len_a, $len_b);
				 }
			} elsif( $th < 0 && defined($t_a[$i+1]) ) {	
				 my $th_a = computTH($t_a[$i]." ".$t_a[$i+1], $t_b[$i], $len_a, $len_b);

				 if( abs($th_a) < $limit ) {
				 	 (@t_a) = mergeSentance(\@t_a, $i, $i+1);
				 	 $th = computTH($t_a[$i], $t_b[$i], $len_a, $len_b);
				 } elsif( $th_a < 0 ) {
				 	 (@t_a) = mergeSentance(\@t_a, $i, $i+1);
				 	 $th = computTH($t_a[$i], $t_b[$i], $len_a, $len_b);
				 }
			}
		}
	
		push(@th_list, $th);	
#		print "$th\n$t_a[$i]\n$t_b[$i]\n\n";

#		my $l_a = sprintf("%2.1f", length($t_a[$i])/$len_a*100);
#		my $l_b = sprintf("%2.1f", length($t_b[$i])/$len_b*100);

#		print "$th\n$l_a:$t_a[$i]\n$l_b:$t_b[$i]\n\n";
	}
	
	(@t_a) = removeEmptyLine(@t_a);
	(@t_b) = removeEmptyLine(@t_b);

	return (\@t_a, \@t_b, @th_list);
}
#====================================================================
sub computTH {
	my ($_a, $_b, $_len_a, $_len_b) = @_;
	
	return 99 if( length($_a) == 0 || length($_b) == 0 );
	
	my $l_a = sprintf("%2.1f", length($_a)/$_len_a*100);
	my $l_b = sprintf("%2.1f", length($_b)/$_len_b*100);
	
	return sprintf("%2.1f", $l_a - $l_b);
}
#====================================================================
sub removeEmptyLine {
	my (@_list) = @_;
	
	my (@ret) = ();
	foreach my $line ( @_list ) {
		next if( !defined($line) );	

		$line =~ s/^\s+|\s+$//g;
		
		next if( $line eq "" );	
		
		push(@ret, $line);
	}
	
	return (@ret);
}
#====================================================================
sub mergeSentance {
	my ($_list, $_st, $_en) = @_;
	
	my (@ret) = ();
	
	for( my $i=0 ; $i<$_st ; $i++ ) {push(@ret, $_list->[$i])}
	
	my $buf = "";
	for( my $i=$_st ; $i<=$_en ; $i++ ) {$buf .= $_list->[$i]." " if( defined($_list->[$i]))}
	
	$buf =~ s/\s+$//;
	push(@ret, $buf);

	for( my $i=$_en+1 ; $i<scalar(@{$_list}) ; $i++ ) {push(@ret, $_list->[$i]) if( defined($_list->[$i]))}
		
	return (@ret);
}
#====================================================================
sub trimDonga {
	my (@list) = @_;

	my (%idx, @ret) = ();
	foreach my $line ( @list ) {
		$line =~ s/^\s+|\s+$//g;

		# APRIL 21, 2010 04:51
		# 전영한 (scoopjyh@donga.com)
		# 박재명  김지현 (jmpark@donga.com jhk85@donga.com)
		# Editorial Writer Lee Jeong-hoon (hoon@donga.com)	이 정 훈 논설위원 hoon@donga.com
		# 육 정 수 논설위원 sooya@donga.com

		if( $line =~ /^\d+$/ ||
			$line =~ /\w+ \d{2,2}, (20\d{2,2}) \d{2,2}:\d{2,2}/ ||
			$line =~ /^(.{2,3}\s*){1,3}\((.+?\@donga\.com\s*)+\)$/ ||
			$line =~ /^(.\s*){2,3}\s*.{4,4}\s*.+?\@donga\.com$/ ||
			$line =~ /^Editorial Writer .+\(.+?\@donga\.com\)$/
			) {
#			print STDERR "# line removed: $line \n";
			next;
		}


		last if( defined($idx{$line}) );

		push(@ret, $line);
		$idx{$line} = 1;
	}

	return (@ret);
}
#====================================================================
sub splitParagraph {
	my ($_a, $_b) = (@_);

	my (@ret_a, @ret_b) = ();

	push(@ret_a, $_a);
	push(@ret_b, $_b);

	# split
	$_a =~ s/\.\s*/\.\n/g;
	$_b =~ s/\.\s*/\.\n/g;

	# merge
	$_a =~ s/(\d+\.)\n(\d+)|(\W+\.)\n(\W+)/$1$2/g;
	$_b =~ s/(\d+\.)\n(\d+)|(\W+\.)\n(\W+)/$1$2/g;

	my (@t_a) = split(/\n/, $_a);
	my (@t_b) = split(/\n/, $_b);

	return (\@ret_a, \@ret_b) if( scalar(@t_a) == 1 || scalar(@t_a) != scalar(@t_b) );

	# check length
	for( my $i=0 ; $i<scalar(@t_a) ; $i++ ) {
		my $len_a = sprintf("%2.1f", length($t_a[$i])/length($_a)*100);
		my $len_b = sprintf("%2.1f", length($t_b[$i])/length($_b)*100);

		my $th = abs($len_a - $len_b);

		return (\@ret_a, \@ret_b) if( $th > 20 );
	}

	(@ret_a, @ret_b) = ();

	print STDERR "SPLIT:(",scalar(@t_a),") ============================ \n";
	print STDERR join(" ", @t_a), "\t", join(" ", @t_b), "\n\n";

	for( my $i=0 ; $i<scalar(@t_a) ; $i++ ) {
		my $len_a = sprintf("%2.1f", length($t_a[$i])/length($_a)*100);
		my $len_b = sprintf("%2.1f", length($t_b[$i])/length($_b)*100);

		my $th = sprintf("%2.1f", abs($len_a - $len_b));

		print STDERR "$th\n$t_a[$i]\n$t_b[$i]\n\n";

		push(@ret_a, $t_a[$i]);
		push(@ret_b, $t_b[$i]);
	}

	return (\@ret_a, \@ret_b);
}
#====================================================================
sub mergeCnnBitext {
	my $a = $args{a};
	my $b = $args{b};
	my $c = $args{align_info};

	my (%align) = readAlignInfo($c);

	my (%text_a) = readTextFile($a);
	my (%text_b) = readTextFile($b);

	print STDERR "$a:\t".scalar(keys %text_a)."\n";
	print STDERR "$b:\t".scalar(keys %text_b)."\n";

	foreach my $k ( keys %text_a ) {
		if( !defined($align{$k}) || !defined($text_b{$align{$k}}) ) {
			print STDERR "# ERROR ALIGN: $k\n";
			next;
		}

		my (@list_a) = split(/\n/, $text_a{$k});
		my (@list_b) = split(/\n/, $text_b{$align{$k}});

		my $max = ( scalar(@list_a)>scalar(@list_b) ) ? scalar(@list_a) : scalar(@list_b);

		$k =~ s/^.+=//;

		for( my $i=0 ; $i<$max ; $i++ ) {
			my $str_a = ( defined($list_a[$i]) ) ? $list_a[$i] : "NULL";
			my $str_b = ( defined($list_b[$i]) ) ? $list_b[$i] : "NULL";

			last if( $str_a =~ /\p{Hangul}/ );
			last if( $str_b !~ /\p{Hangul}/ );

			if( $str_a =~ /^.*?\(CNN\) -+ / ) {
				print STDERR "Remove tag: $str_a ==> ";

				$str_a =~ s/^.*?\(CNN\) -+ //;
				print STDERR "$str_a\n\n";
			}

			# split n:n
			my ($list_a, $list_b) = splitParagraph($str_a, $str_b);

			for( my $j=0 ; $j<scalar(@{$list_a}) ; $j++ ) {
				print "$k\t$list_a->[$j]\t$list_b->[$j]\n"
			}
		}

		print "\n\n";
	}
}
#====================================================================
sub readAlignInfo {
	my ($_fn) = @_;

	my ($file) = ();

	my ($open_mode) = ("<");
	$open_mode = "<:gzip" if( $_fn =~ /\.gz$/ );

	die "$_fn\n" unless( open($file, $open_mode, $_fn) );

	binmode($file, ":utf8");

	my (%align) = ();
	foreach my $line ( <$file> ) {
		$line =~ s/^\s+|\s+$//g;

		last if( $line eq "#__END__" );
		next if( $line =~ /^#/ || $line eq "" );

		my ($s, $t) = split(/\t/, $line, 3);

#		$s =~ s/^.+=(\d+)$/$1/;
#		$t =~ s/^.+=(\d+)$/$1/;

		$align{$s} = $t;
	}

	close($file);

	return (%align);
}
#====================================================================
sub readTextFile {
	my ($_fn) = (@_);

	my $file;

	my ($open_mode) = ("<");
	$open_mode = "<:gzip" if( $_fn =~ /\.gz$/ );
	die "$_fn\n" unless( open($file, $open_mode, $_fn) );

	binmode($file, ":utf8");

	my $url = "";
	my (%text) = ();
	
	use utf8;
	
	no warnings;
			
	foreach my $line ( <$file> ) {
		$line =~ s/^\s+|\s+$//g;

		last if( $line eq "#__END__" );
		next if( $line =~ /^#/ || $line eq "" );

		my ($a, $b, $c) = split(/\t/, $line, 3);

		if( !defined($c) ) {
			next;
		}

		$c =~ s/^\s+|\s+$//g;
		
		$c =~ s/¡¯¡¯/\"/g;
		$c =~ s/¡¯/\'/g;

		if( $c !~ /\p{Hangul}/ ) {
			$c =~ s/\x91|\x92/\'/g;
			$c =~ s/\x93|\x94/\"/g;
		}

		next if $c eq "";

		if( $b eq "0" ) {
			$url = $c;
			next;
		}

		$text{$url} .= $c."\n";
	}

	use warnings;

	close($file);

	return (%text);
}
#====================================================================
sub removeLine {
	my (%line_index) = map {$_ => 1} readData($args{remove_line});

	print STDERR "$args{remove_line}:\t".scalar(keys %line_index)."\n";

	foreach my $line ( <STDIN> ) {
		$line =~ s/^\s+//;

		last if( $line eq "#__END__" );
		next if( $line =~ /^#/ || $line eq "" );

		my ($a, $b, $c) = split(/\t/, $line, 3);

		next if( !defined($c) );

		if( defined($line_index{$c}) ) {
#			print STDERR "Line Removed: $line\n";
			next;
		}

		print "$a\t$b\t$c";
		print STDERR "\r($a)";
	}
}
#====================================================================
sub extractText {
	my $cnt = 0;
	
	no warnings;
	foreach my $line ( <STDIN> ) {
		$line =~ s/^\s+|\s+$//g;

		last if( $line eq "#__END__" );
		next if( $line =~ /^#/ || $line eq "" );

		$line =~ s/<NEW_LINE>|<!--NEW_LINE-->/\n/g;
		my $html = $line;

		my ($text, $url) = GetText(\$html);

		my $line_no = 0;

		print "$cnt\t$line_no\t$url\n";
		foreach my $str ( split(/\n/, $text) ) {
			$line_no++;
			
			$str =~ s/\x93|\x94/\"/g;
			$str =~ s/\x91|\x92/\'/g;
						
			print "$cnt\t$line_no\t$str\n";
		}

		print STDERR "\r($cnt)";
		$cnt++;
	}
	use warnings;
}
#====================================================================
sub extractLink {
	my $cnt = 0;
	foreach my $line ( <STDIN> ) {
		$line =~ s/^\s+|\s+$//g;

		last if( $line eq "#__END__" );
		next if( $line =~ /^#/ || $line eq "" );

		$line =~ s/<NEW_LINE>|<!--NEW_LINE-->/\n/g;
		my $html = $line;

		my (%link_list) = GetLink(\$html, "a", "href");

		# $html = $line;
		# (%link_list) = (%link_list, GetLink(\$html, "img", "onclick"));

		foreach my $text ( keys %link_list ) {
			foreach my $url ( keys %{$link_list{$text}} ) {
				print join("", keys %{$link_list{_URL}})."\t".$url."\t".$text."\n";
			}
		}

		print STDERR "\r($cnt)";
		$cnt++;
	}
}
#====================================================================
sub getPage {
	use DBI;
	
	binmode(STDERR, ":utf8");
	
	my $_timeout = ( defined($args{timeout}) ) ? $args{timeout} : 20;
	my $_try 	 = ( defined($args{try}) )     ? $args{try}     : 1;
	my $_sleep 	 = ( defined($args{sleep}) )   ? $args{sleep}   : 5;
	
	my $_fn_url_db = ( defined($args{fn_url_db}) ) ? $args{fn_url_db} : "";
	
	# create table
	my $dbh;
	if( $_fn_url_db ne "" && !-e $_fn_url_db ) {
	    $dbh = DBI->connect("dbi:SQLite:dbname=$_fn_url_db","","",{AutoCommit => 1, PrintError => 1});
	
		my $query = "CREATE TABLE IF NOT EXISTS url_list (url TEXT, m_date DATE DEFAULT (datetime('now','localtime')))";
		
		print STDERR "($_fn_url_db) query: $query\n";
	    my $sth = $dbh->prepare($query);
	    
	    $sth->execute;
	
		$sth->finish;
#	    $dbh->disconnect();
	} else {
		if( $_fn_url_db ne "" && -e $_fn_url_db ) {
		    $dbh = DBI->connect("dbi:SQLite:dbname=$_fn_url_db","","",{AutoCommit => 1, PrintError => 1}) or $dbh = undef;
		}
	}

	no warnings "utf8";

	my (@url_list) = ();
	foreach my $url ( <STDIN> ) {
		$url =~ s/^\s+|\s+$//g;
		
		last if( $url eq "#__END__" );
		next if( $url =~ /^#/ || $url eq "" );

		push(@url_list, $url);
	}

	my $cnt = 0;
	foreach my $url ( @url_list ) {
		print STDERR BOLD, BLUE, "\n# $url (".sprintf("%d/%d", $cnt, scalar(@url_list)).")\n", RESET;
		$cnt++;

		my ($a, $b) = split(/\t/, $url);
		$url = $a;

		$b = "" if( !defined($b) );
		$b = "" if( $b =~ /^#/ );

		# check downloaded url 
		if( defined($dbh) ) {
			my $url_lo = $url;
			$url_lo = "$url?$b" if( $b ne "" );			
			
			$url_lo =~ s/\'/\'\'/g;
			my $query = "SELECT url FROM url_list WHERE url = '$url_lo'";
			
			print STDERR "($_fn_url_db) query: $query\n";
		    my $sth = $dbh->prepare($query);
		    
		    $sth->execute;
		    
		    my $ref = $sth->fetchall_arrayref;
		    
			$sth->finish;

			my $ret = 0;
			$ret = 1 if( scalar(@{$ref}) > 0 );
		
		    if( $ret ) {
				print STDERR BOLD, BLUE, "\n# already downloaded: $url\n", RESET;
		    	next;
		    }
		}

		my ($html, $err) = getWebPage($url, $b, $_timeout, $_try);

		print STDERR "# RESULT:\t$err\t$url\t$b\n";

		$html =~ s/\r\n/<!--NEW_LINE-->/g;
		$html =~ s/\n/<!--NEW_LINE-->/g;

		$b = "?$b" if( $b ne "" );
		
		$url = "$url$b";
		print "<!-- ## URL: $url --><!--NEW_LINE-->$html\n";

		# update downloaded url 
		if( defined($dbh) ) {
			$url =~ s/\'/\'\'/g;
			my $query = "INSERT INTO url_list (url) VALUES ('$url')";
			
			print STDERR "($_fn_url_db) query: $query\n";
		    my $sth = $dbh->prepare($query);
		    
		    $sth->execute;
			$sth->finish;
		}

		my $sleep_time = int(rand(5) + $_sleep);
		print STDERR "# SLEEP: $sleep_time\n";
		Time::HiRes::sleep($sleep_time);
	}
	
	if( defined($dbh) ) {
	    $dbh->disconnect();
	}
}
#====================================================================
sub readData {
	my ($_fn) = @_;

    my (@ret) = ();
	foreach my $fn ( split(/,/, $_fn) ) {
		if( $fn =~ /\.db$/ ) {
#			my $_table_name = "twitter";
#
#		    my $dbh = DBI->connect("dbi:SQLite:dbname=$fn","","",{AutoCommit => 1, PrintError => 1});
#
#			my $query = "SELECT * FROM $_table_name";
#		    my $sth = $dbh->prepare($query);
#
#			while( my @data = $sth->fetchrow_array() ) {
#				push(@ret, join('\t', @data));
#			}
#
#			$sth->finish;
#
#		    $dbh->disconnect();
		} else {
			my $open_mode = "<";
			$open_mode = "<:gzip" if( $fn =~ /\.gz$/ );

			return () unless( open(FILE, $open_mode, $fn) );

			binmode(FILE, ":utf8");

			push(@ret, <FILE>);

			close(FILE);
		}
	}

	return (@ret);
}
#====================================================================
sub getWebPage {
	my ($_url, $_post_data, $_timeout, $_try) = @_;

	$_try = 1  if( !defined($_try) || $_try eq "" );
	$_try = 10 if( !defined($_timeout) || $_timeout eq "" );

	my $fn = $_url;
	$fn =~ s/(:|\/|\?|\&|=|\#|\-|\+)+/_/g;

	my $uid = strftime('%Y-%m-%d_%H.%M.%S', localtime).".".uniqid;

	my $fn_a = "/tmp/a_$uid";
	my $fn_b = "/tmp/b_$uid";

	$_post_data = "" if( !defined($_post_data) );
	$_post_data = "--post-data \"$_post_data\"" if( $_post_data ne "" );

	my $cmd = "wget -k --tries $_try --timeout $_timeout \"$_url\" $_post_data -O\"$fn_a\" 2> \"$fn_b\"";

	safeSystem($cmd);

	my (@stdout) = readHtmlFile($fn_a);
	my (@stderr) = readHtmlFile($fn_b);

	safeSystem("rm -f \"$fn_a\" \"$fn_b\"");

	my $html = join("\n", @stdout);
	$html =~ s/\&\#(\d+)\;/chr($1)/eg;

	my $str_err = join("\n", @stderr);
	my $error_msg = "";

	$error_msg = "OK" 			if( index($str_err, "HTTP request sent, awaiting response... 200 OK") > 0 );
	$error_msg = "Bad Request" 	if( index($str_err, "HTTP request sent, awaiting response... 400 Bad Request") > 0 );
	$error_msg = "Not Found" 	if( index($str_err, "HTTP request sent, awaiting response... 404 Not Found") > 0 );

	print STDERR "# Get Web Page error_msg: $error_msg\n";

	return ($html, $error_msg);
}
#====================================================================
sub readHtmlFile {
	my ($_fn, $_encoding) = @_;

    my (@ret) = ();

	my $open_mode = "<";
	$open_mode = "<:gzip" if( $_fn =~ /\.gz$/ );

	if( defined($_encoding) && $_encoding ne "" ) {
		$open_mode = "<:encoding($_encoding)";
	} else {
		my $charset = `grep charset= $_fn`;
		$open_mode = "<:encoding($1)" if( $charset =~ /charset=([^\"\'> ]+)(\"|\'|>| )/ );

		print STDERR "# charset: $charset\n";
	}

	print STDERR "# Open Mode: $open_mode\n";

	return () unless( open(FILE, $open_mode, $_fn) );

	binmode(FILE, ":utf8");

	no warnings;

	push(@ret, <FILE>);

	use warnings;

	close(FILE);

	return (@ret);
}
#====================================================================
sub GetText
{
	my ($_fn) = @_;

	my $p = HTML::TokeParser->new($_fn) || return "";

	my (%tag_opt_s) = qw/ p n div n li n h1 n h2 n h3 n dt n br n hr n   ul n /;
	my (%tag_opt_e) = qw/ p n div n li n h1 n h2 n h3 n ul n br n span s ul s tr n td s /;

	foreach my $tag ( keys %tag_opt_s ) {
		if( $tag_opt_s{$tag} eq "n" ) {$tag_opt_s{$tag} = "\n"}
		if( $tag_opt_s{$tag} eq "s" ) {$tag_opt_s{$tag} = " "}
	}

	foreach my $tag ( keys %tag_opt_e ) {
		if( $tag_opt_e{$tag} eq "n" ) {$tag_opt_e{$tag} = "\n"}
		if( $tag_opt_e{$tag} eq "s" ) {$tag_opt_e{$tag} = " "}
	}

	my ($buf, $url) = ("", "");
	while( my $token = $p->get_token ) {
		my ($ttype, $tag) = @{$token};

		if( $ttype eq "S" ) {
			# start tag
			my ($ttype, $tag, $attr, $attrseq, $rawtxt) = @{$token};

			$tag =~ s/\/$//;

			$p->get_trimmed_text("/".$tag) if( $tag eq "script" );
			$p->get_trimmed_text("/".$tag) if( $tag eq "style"  );

#			if( $tag eq "meta" ) {
#				$buf .= "\n";
#				foreach my $key ( keys %$attr ) {
#					if( $key eq "/" ) {next}
#					$buf .= "## META: ".$key."\t".$attr->{$key}."\n";
#				}
#			}
#
#			if( $tag eq "title" ) {
#				$buf .= "\n";
#				$buf .= "## TITLE: ".$p->get_trimmed_text("/".$tag)."\n";
#			}

#			print $tag."\n";

			$buf .= $tag_opt_s{$tag} if( defined($tag_opt_s{$tag}) );
		} elsif( $ttype eq "E" ) {
			# end tag
			my ($ttype, $tag, $text) = @{$token};

			$buf .= $tag_opt_e{$tag} if( defined($tag_opt_e{$tag}) );
		} elsif( $ttype eq "T" ) {
			# text
			my ($ttype, $text, $is_data) = @{$token};

#			print $text."\n";

			$buf .= $text;
		} elsif( $ttype eq "C" ) {
			# comment
			my ($ttype, $text) = @{$token};

			$url = $1 if( $text =~ /^<!-- \#\# URL: (.+) -->/ );
		}
	}

	$buf =~ s/&nbsp;/ /g;
	$buf =~ s/&\#(\d+?);/chr($1)/eg;

	return ($buf, $url);
}
#====================================================================
sub GetLink
{
	my ($_fn, $_tag_name, $_tag_attr) = @_;

	$_tag_name = "a"    if( !defined($_tag_name) || $_tag_name eq "" );
	$_tag_attr = "href" if( !defined($_tag_attr) || $_tag_attr eq "" );

	my $p = HTML::TokeParser->new($_fn) || return "";

	my (%link_list, $base_url, $base_url_root) = ();
	while( my $token = $p->get_token ) {
		my $ttype = shift @{$token};

		if( $ttype eq "S" ) {
			my ($tag, $attr, $attrseq, $rawtxt) = @{$token};

			if( $tag eq $_tag_name ) {
				my $attr_value = $attr->{$_tag_attr};

				next if( !defined($attr_value) || $attr_value eq "" );

				my $encl = $p->get_trimmed_text("/".$tag);

#				print "encl($tag):".$encl;

				if( $attr_value !~ /^javascript:/i && $attr_value !~ /^http:\/\// && defined($base_url) ) {
					if( $attr_value =~ /^\/+/ ) {
						$attr_value =~ s/^\/+//;
						$attr_value = $base_url_root."/".$attr_value;
					} else {
						$attr_value = $base_url."/".$attr_value;
					}
				}

				$link_list{$encl}{$attr_value} = 1;
			}
		} elsif( $ttype eq "C" ) {
			my ($comment) = @{$token};

			if( !defined($link_list{_BASE_URL}) && $comment =~ /^<!-- \#\# URL: (.+) -->/ ) {
				if( defined($1) ) {$base_url = $1}

				$link_list{_URL}{$base_url} = 1;

				$base_url =~ s/^(http:\/\/.+)\/[^\/]+?$/$1/;
				$base_url =~ s/\/+$//;

				$base_url_root = $base_url;
				$base_url_root =~ s/^(http:\/\/.+?)\/.+$/$1/;

				$link_list{_BASE_URL}{$base_url} = 1;
				$link_list{_BASE_URL_ROOT}{$base_url_root} = 1;
			}
		}
	}

	return (%link_list);
}
#====================================================================
sub tag2text {
	my (%tag_replace) = (
		'&nbsp;' =>' ', 
		'&lt;' => '<', 
		'&gt;' => '>', 
		'&amp;' => '&', 
		'&quot;' => '"',
		'&copy;' => '(C)',
		'&hellip;' => '...',
		'&ldquo;' => '"',
		'&rdquo;' => '"',
		'&middot;' => '-',
		'&#8226;' => '-',
	);
	
	no warnings;

	foreach my $line ( <STDIN> ) {
		$line =~ s/(\&[^;]+\;*)/$tag_replace{$1} if defined($tag_replace{$1})/eg;	
		
		print $line;
	}
}
#====================================================================
sub print_r {
    package print_r;
    our $level;
    our @level_index;
    if ( ! defined $level ) { $level = 0 };
    if ( ! defined @level_index ) { $level_index[$level] = 0 };

    for ( @_ ) {
        my $element = $_;
        my $index   = $level_index[$level];

        print "\t" x $level . "[$index] => ";

        if ( ref($element) eq 'ARRAY' ) {
            my $array = $_;

            $level_index[++$level] = 0;

            print "(Array)\n";

            for ( @$array ) {
                main::print_r( $_ );
            }
            --$level if ( $level > 0 );
        } elsif ( ref($element) eq 'HASH' ) {
            my $hash = $_;

            print "(Hash)\n";

            ++$level;

            for ( keys %$hash ) {
                $level_index[$level] = $_;
                main::print_r( $$hash{$_} );
            }
        } else {
            print "$element\n";
        }

        $level_index[$level]++;
    }
} # End print_r
#====================================================================

__END__








