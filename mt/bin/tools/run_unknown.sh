

export tools=`pwd`

export src=en
export trg=ko

export test_set=test

    for i in $(seq 0 9); do


export model_path=WIT.en-ko.short.sentbleu_tuning/full_set.model/model.$i

cat $model_path/data/test.en-ko.out \
   | perl ./matching_unknown.pl -dict wiki/ko-en.all.txt \
   > $model_path/data/test.en-ko.out.wiki_apply \
   2> $model_path/data/test.en-ko.out.wiki_apply.cnt

export data_path=$model_path/data

perl $tools/wrap.pl -type tst \
  -in $data_path/$test_set.$src-$trg.out.wiki_apply \
  -out $data_path/$test_set.$src-$trg.out.sgm

sync

$SCRIPTS_ROOTDIR/mteval-v11b.pl \
  -s $data_path/$test_set.$src-$trg.$src.sgm \
  -r $data_path/$test_set.$src-$trg.$trg.sgm \
  -t $data_path/$test_set.$src-$trg.out.sgm \
  | tee $data_path/$test_set.$src-$trg.out.wiki_apply.bleu

sync

    done

