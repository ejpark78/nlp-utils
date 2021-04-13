

g_smt_home=/home/ejpark/workspace/model/ko-cn/tm-200.exclude

make_hybrid_feature.pl \
    -phrase_prob $g_smt_home/phrase-table.leveldb \
    -lex $g_smt_home/lex.e2f.leveldb \
    -lm_f $g_smt_home/lm/train.ko.lm.leveldb \
    -lm_e $g_smt_home/lm/train.cn.lm.leveldb 

