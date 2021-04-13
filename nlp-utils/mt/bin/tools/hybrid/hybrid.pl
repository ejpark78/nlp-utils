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

	"debug" => \$args{"debug"}
);
#====================================================================
# MAIN
#====================================================================
main: {
	binmode(STDIN, "utf8");
	binmode(STDOUT, "utf8");
	binmode(STDERR, "utf8");

	my $log_dir = $args{"log_dir"};
	my $url = $args{"smt_url"};

	my (%pid) = ();

	print STDERR "# init_tagging_ko\n";
	my ($STDIN_TAGGING_KO, $STDOUT_TAGGING_KO) = init_tagging_ko($log_dir, \%pid);

	print STDERR "# init_mlt_kc\n";
	my ($STDIN_MLT_KC, $STDOUT_MLT_KC) = init_mlt_kc($log_dir, \%pid);

	print STDERR "# init_segmenter_cn\n";
	my ($STDIN_SEGMENTER_CN, $STDOUT_SEGMENTER_CN) = init_segmenter_cn($log_dir, \%pid);

	print STDERR "# init svm\n";
	my $svm = new Algorithm::SVM("Model" => "/home/ejpark/workspace/model/hybrid/model/train-02.bleu-0.65.model");

	my (%db) = ();
	$db{"lex"} = new Tie::LevelDB::DB($args{"lex"}) if( -e $args{"lex"} );

	$db{"lm_f"} = new Tie::LevelDB::DB($args{"lm_f"}) if( -e $args{"lm_f"} );
	$db{"lm_e"} = new Tie::LevelDB::DB($args{"lm_e"}) if( -e $args{"lm_e"} );

	$db{"lm_backoff_f"} = new Tie::LevelDB::DB($args{"lm_backoff_f"}) if( -e $args{"lm_backoff_f"} );
	$db{"lm_backoff_e"} = new Tie::LevelDB::DB($args{"lm_backoff_e"}) if( -e $args{"lm_backoff_e"} );

	$db{"phrase_prob"} = new Tie::LevelDB::DB($args{"phrase_prob"}) if( -e $args{"phrase_prob"} );

	my $json = JSON->new->allow_nonref;
	while( my $text = <STDIN> ) {
		$text =~ s/\s+$//;

		# token ko
		my $tagged_text = "";
		print $STDIN_TAGGING_KO $text."\n";	
		while( defined($tagged_text=<$STDOUT_TAGGING_KO>) ) {
			$tagged_text =~ s/\s+$//;
			last;
		}

		my $text_tok = $tagged_text;
		$text_tok =~ s/\/[^ ]+|\s+$//g;

		# translate smt
		my ($smt, @phrase_log) = translate_smt($url, $text_tok, $args{"src"}, $args{"trg"});

		# trasnlate lbmt
		my $lbmt = "";
		print STDIN_MLT_KC $text."\n";	
		while( !defined($lbmt=<STDOUT_MLT_KC>) ) {
			$lbmt =~ s/\s+$//;
			last;
		}

		# token cn
		my $lbmt_tok = "";
		print $STDIN_SEGMENTER_CN $lbmt."\n";	
		while( !defined($lbmt_tok=<$STDOUT_SEGMENTER_CN>) ) {
			$lbmt_tok =~ s/\s+$//;
			last;
		}

		# svm
		$smt =~ s/\|UNK//g;
		my (%features) = (
			"class" => 1,
			"source" => $text,
			"smt" => $smt,
			"lbmt" => $lbmt_tok,
			"tagged_text" => $tagged_text,
			"phrase_log" => \@phrase_log
		);		

		my $svm_feature = $json->ascii(1)->encode(\%features);
		my ($input, $result) = make_hybrid_feature($json, $svm_feature, \%db);	

		# scale

		# predict
		my $ds = new Algorithm::SVM::DataSet("Label" => 1, "Data" => \@{$result});
		my $predict = $svm->predict($ds);

		print "predict: $predict\n";
	}

	close($STDIN_TAGGING_KO);
	close($STDOUT_TAGGING_KO);

	close($STDIN_MLT_KC);
	close($STDOUT_MLT_KC);

	close($STDIN_SEGMENTER_CN);
	close($STDOUT_SEGMENTER_CN);

	close(FILE_LOG);
}
#====================================================================
# sub functions
#====================================================================
__END__