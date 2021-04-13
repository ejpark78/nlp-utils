

g_smt_home=~/workspace/model/ko-cn/tm-200.exclude

hybrid-web.pl \
    -port 99134 \
    -phrase_prob $g_smt_home/phrase-table.leveldb \
    -lex $g_smt_home/lex.e2f.leveldb \
    -lm_f $g_smt_home/lm/train.ko.lm.leveldb \
    -lm_e $g_smt_home/lm/train.cn.lm.leveldb 


# cat test_web.txt \
#   | hybrid-web.pl \
#     -log_dir log \
#     -phrase_prob $g_smt_home/phrase-table.leveldb \
#     -lex $g_smt_home/lex.e2f.leveldb \
#     -lm_f $g_smt_home/lm/train.ko.lm.leveldb \
#     -lm_e $g_smt_home/lm/train.cn.lm.leveldb 
  # > predict
