#!/usr/bin/env perl
#!/usr/bin/perl
#====================================================================
use strict;
use Encode;
use XMLRPC::Lite;
use utf8;
use IPC::Open2;
use IPC::Open3;
use FileHandle;
use JSON;
use Getopt::Long;
use Tie::LevelDB;
use Data::Dumper;

use Algorithm::SVM;
use Algorithm::SVM::DataSet;

use POSIX qw(strftime);
use IO::Socket;
use Net::hostent;		# for OO version of gethostbyaddr
use Sys::AlarmCall;

use FindBin qw($Bin);
use lib "$Bin";

require "hybrid.pm";
#====================================================================
my (%args) = (
	"smt_url" => "http://localhost:9004/RPC2",
	"src" => "ko",
	"trg" => "cn",
);

GetOptions(
	"log_dir=s" => \$args{"log_dir"},
	
	"src=s" => \$args{"src"},
	"trg=s" => \$args{"trg"},

	"lm_f=s" => \$args{"lm_f"},
	"lm_e=s" => \$args{"lm_e"},

	"backoff_f|lm_backoff_f=s" => \$args{"lm_backoff_f"},
	"backoff_e|lm_backoff_e=s" => \$args{"lm_backoff_e"},

	"lex=s" => \$args{"lex"},
	"phrase_prob=s" => \$args{"phrase_prob"},

	"port=s" => \$args{"port"},

	"debug" => \$args{"debug"}
);
#====================================================================
# MAIN
#====================================================================
main: {
	binmode(STDIN, "utf8");
	binmode(STDOUT, "utf8");
	binmode(STDERR, "utf8");

	my (%pid, %daemon) = ();

	print STDERR "# init_segmenter_cn\n";
	my ($STDIN_SEGMENTER_CN, $STDOUT_SEGMENTER_CN) = init_segmenter_cn("", \%pid);

	$daemon{"STDIN_SEGMENTER_CN"} = $STDIN_SEGMENTER_CN;
	$daemon{"STDOUT_SEGMENTER_CN"} = $STDOUT_SEGMENTER_CN;

	print STDERR "# init svm\n";
	my $svm = new Algorithm::SVM("Model" => "/home/ejpark/workspace/model/hybrid/model/train-02.bleu-0.65.model");

	my (%db) = ();
	$db{"lex"} = new Tie::LevelDB::DB($args{"lex"}) if( -e $args{"lex"} );

	$db{"lm_f"} = new Tie::LevelDB::DB($args{"lm_f"}) if( -e $args{"lm_f"} );
	$db{"lm_e"} = new Tie::LevelDB::DB($args{"lm_e"}) if( -e $args{"lm_e"} );

	$db{"lm_backoff_f"} = new Tie::LevelDB::DB($args{"lm_backoff_f"}) if( -e $args{"lm_backoff_f"} );
	$db{"lm_backoff_e"} = new Tie::LevelDB::DB($args{"lm_backoff_e"}) if( -e $args{"lm_backoff_e"} );

	$db{"phrase_prob"} = new Tie::LevelDB::DB($args{"phrase_prob"}) if( -e $args{"phrase_prob"} );

	#====================================================================
	my $server = IO::Socket::INET->new("Proto" => "tcp", "LocalPort" => $args{"port"}, "Listen" => SOMAXCONN, "Reuse" => 1) or die "#ERROR: Could not create socket: $!\n";
	
	if( !defined($server) ) {
		print "#ERROR: server init failed.\n";
		exit;	
	}
	
	my $client;
	my $json = JSON->new->allow_nonref;

	while( my $client_addr = accept($client, $server) ) {
		my($port, $iaddr) = sockaddr_in($client_addr);
		my $name = gethostbyaddr($iaddr,AF_INET);
		
		my $pid_client = fork();
		
		if( $pid_client == 0 ) {
			&run_client($client, $json, $svm, \%db, \%daemon);
			exit(0);   # Child process exits when it is done.
		}
	
		waitpid($pid_client, 0);
		
		close $client;
	}
	#====================================================================

	close($STDIN_SEGMENTER_CN);
	close($STDOUT_SEGMENTER_CN);

	# close($STDIN_SVM_SCALE);
	# close($STDOUT_SVM_SCALE);
}
#====================================================================
# sub functions
#====================================================================
sub run_client
{
	my $client = shift(@_);
	my $json = shift(@_);
	my $svm = shift(@_);
	my $db = shift(@_);
	my $daemon = shift(@_);

	my $STDIN_SEGMENTER_CN = $daemon->{"STDIN_SEGMENTER_CN"};
	my $STDOUT_SEGMENTER_CN = $daemon->{"STDOUT_SEGMENTER_CN"};

	print "\n\n##############################################################\n";
	print "# New Client: \n";
	
	$client->autoflush(1);

	my $buf = "";
	while( my $line = <$client> ){
		print "Client In: ".$line."\n";

		$buf .= $line."\t";
		if( $line =~ /<\/PACKET>/ ) {last}
	}

	# <PACKET> 나는 학생이다.  </PACKET>
	
	$buf = StripTag(\$buf, "<PACKET>", "</PACKET>");
	
	# check daemon management command
	if( $buf =~ /<STOP>/ ) {
		# die "Stop Daemon: $_args->{main_pid}\n";
		# exit(1);	
	}
	

	my (%input) = ();
	my $decoded = $json->decode( $buf );
	# print Dumper($decoded) if( $args{"debug"} );

	print STDERR "### json in\n";
	foreach my $k ( sort keys %{$decoded} ) {
		print STDERR "# $k => $decoded->{$k}\n";
	}

	$input{"class"} = $decoded->{"class"};
	$input{"src"} = $decoded->{"source"};
	$input{"tst_smt"} = $decoded->{"smt"};
	$input{"tst_lbmt"} = $decoded->{"lbmt"};
	$input{"tagged_text"} = $decoded->{"tagged_text"};
	$input{"phrase_log"} = $decoded->{"phrase_log"};

	my $tok_text = $decoded->{"tagged_text"};
	$tok_text =~ s/\/[^ ]+|\s+$//g;

	# token cn
	my $lbmt_tok = "";
	print $STDIN_SEGMENTER_CN $input{"tst_lbmt"}."\n";	
	while( !defined($lbmt_tok=<$STDOUT_SEGMENTER_CN>) ) {
		$lbmt_tok =~ s/\s+$//;
		last;
	}

	# svm
	$input{"tst_smt"} =~ s/\|UNK//g;
	my (%features) = (
		"class" => 1,
		"source" => $tok_text,
		"smt" => $input{"tst_smt"},
		"lbmt" => $lbmt_tok,
		"tagged_text" => $input{"tagged_text"},
		"phrase_log" => \@{$input{"phrase_log"}}
	);		

	print STDERR "\n### features\n";
	foreach my $k ( sort keys %features ) {
		print STDERR "# $k => $features{$k}\n";
	}

	my $svm_feature = $json->ascii(1)->encode(\%features);
	my ($input, $result) = make_hybrid_feature($json, $svm_feature, $db);	

	# scale
	my (@scale) = (@{$result});
	# my (@scale) = svm_scale($daemon, $result);

	# predict
	my $ds = new Algorithm::SVM::DataSet("Label" => 1, "Data" => \@scale);
	my $predict = $svm->predict($ds);

	if( $predict == 1 ){
		$predict = "smt";
	} else {
		$predict = "lbmt";
	}

	print "predict: $predict\n";
	print $client "<PACKET>$predict</PACKET>\n";

	
	print "\n# Client end\n";
	print "##############################################################\n";
}
#====================================================================
sub svm_scale 
{
	my $daemon = shift(@_);
	my (@features) = (@{shift(@_)});

	my $STDIN_SVM_SCALE = $daemon->{"STDIN_SVM_SCALE"};
	my $STDOUT_SVM_SCALE = $daemon->{"STDOUT_SVM_SCALE"};

	# attach index
	my (@buf) = ();
	push(@buf, "1");
	for( my $i=0 ; $i<scalar(@features) ; $i++ ) {
		push(@buf, sprintf("%d:%s", $i+1, $features[$i]));
	}

	my $str_scaled = "";
	print $STDIN_SVM_SCALE join(" ", @buf)."\n";	
	while( !defined($str_scaled=<$STDOUT_SVM_SCALE>) ) {
		$str_scaled =~ s/\s+$//;
		last;
	}

	# remove index
	my (@ret) = ();
	my (@scale) = split(/\s+/, $str_scaled);
	for( my $i=1 ; $i<scalar(@scale) ; $i++ ) {
		$scale[$i] =~ s/^\d+://;		
		push(@ret, $scale[$i]);
	}

	print STDERR "# svm_scale in: ".join(" ", @buf)."\n";
	print STDERR "# svm_scale out: ".join(" ", @ret)."\n";

	return (@ret);
}
#====================================================================
sub StripTag 
{
	my ($_text, $st_tag, $en_tag) = @_;
	
	my $text = ${$_text};
	my $pos_st_tag = index($text, $st_tag);
	
	return "" if( $pos_st_tag < 0 );
	
	my $pos_en_tag = index($text, $en_tag, $pos_st_tag+length($st_tag)+1);

	return "" if( $pos_en_tag < 0 || $pos_st_tag > length($text) );
	
	my $fragment  = substr($text, $pos_st_tag + length($st_tag), $pos_en_tag - $pos_st_tag - length($st_tag));
	
	${$_text} = substr($text, 0, $pos_st_tag) . substr($text, $pos_en_tag + length($en_tag), length($text));
	
	return $fragment;
}
#====================================================================
__END__