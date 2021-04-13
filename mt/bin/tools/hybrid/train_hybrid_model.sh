

g_smt_home=~/workspace/model/ko-cn/tm-200.exclude
fn=train-data/train-02.tok

cat $fn \
  | cut -f2,3,4,5,6,8,10 \
  | to_json.pl -th 0.65 -seq tagged_text,source,lbmt,smt,phrase_log,smt_bleu,lbmt_bleu \
  > $fn.json

cat $fn.json \
  | make_hybrid_feature.pl \
    -phrase_prob $g_smt_home/phrase-table.leveldb \
    -lex $g_smt_home/lex.e2f.leveldb \
    -lm_f $g_smt_home/lm/train.ko.lm.leveldb \
    -lm_e $g_smt_home/lm/train.cn.lm.leveldb \
  > $fn.svm

cat $fn.svm \
  | cleaning_svm_features.pl \
  > $fn.svm.clean \
  2> $fn.svm.bad

svm-scale -l -1 -u 1 \
  $fn.svm.clean \
  > $fn.svm.clean.scale

svm-train -c 32 -g 0.5 -m 600000 -h 0 \
  $fn.svm.clean.scale \
  model/train-02.bleu-0.65.model


###################################################
# test set

g_smt_home=~/workspace/model/ko-cn/tm-200.exclude
fn=test-data/csli.v1.tok

cat $fn \
  | cut -f1,2,3,4,5,6,7,9 \
  | to_json.pl \
    -th 0.65 \
    -seq source,tagged_text,lbmt,lbmt_score,smt,smt_score,phrase_log,ref \
  > $fn.json

cat $fn.json \
  | make_hybrid_feature.pl \
    -phrase_prob $g_smt_home/phrase-table.leveldb \
    -lex $g_smt_home/lex.e2f.leveldb \
    -lm_f $g_smt_home/lm/train.ko.lm.leveldb \
    -lm_e $g_smt_home/lm/train.cn.lm.leveldb \
  > $fn.svm

cat $fn.svm \
  | cleaning_svm_features.pl \
  > $fn.svm.clean \
  2> $fn.svm.bad

svm-scale -l -1 -u 1 \
  $fn.svm.clean \
  > $fn.svm.clean.scale


########################################################

svm-predict \
  $fn.svm.clean.scale \
  model/train-02.bleu-0.65.model \
  $fn.svm.clean.predict

