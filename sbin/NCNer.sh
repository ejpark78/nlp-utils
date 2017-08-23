#!/usr/bin/env bash


python3 NCNer.py -train_single_model -sample_size -1


python3 NCNer.py -cross_evaluation -sample_size 50000


echo "2014 04 01 19:45 SK 외국인 타자 루크 스캇이 SK 최정에게 원포인트 레슨을 했다." \
    | python3 NCNer.py \
        -stdin \
        -model "model/sample_size=10000/algorithm=lbfgs/fold=full,c1=1.0,c2=0.001,max_itr=50-full.model"

cat "data/baseball.L2.test.train" \
    | python3 NCNer.py \
        -eval \
        -model "model/sample_size=10000/algorithm=lbfgs/fold=full,c1=1.0,c2=0.001,max_itr=50-full.model"

cat "data/baseball.L2.test.train" \
    | python3 NCNer.py \
        -eval \
        -model "model/sample_size=-1/algorithm=lbfgs/fold=-1,c1=1.0,c2=0.001,max_itr=50-full.model"

cat "data/ner.eval.L2.train" \
    | python3 NCNer.py \
        -eval \
        -model "model/sample_size=-1/algorithm=lbfgs/fold=-1,c1=1.0,c2=0.001,max_itr=50-full.model"

cat "data/ner.eval.L2.train" \
    | python3 NCNer.py \
        -eval \
        -model "model/sample_size=-1/algorithm=lbfgs.old/fold=-1,c1=1.0,c2=0.001,max_itr=50-full.model"


python3 NCNer.py -get_features

cat baseball.L2.train.tcsv | perl -ple 's/(PERSON|ORGANIZATION|LOCATION)_.+/$1/;' > baseball.L2.train.2.tcsv



java -mx5g -cp "$scriptdir/stanford-ner.jar:$scriptdir/lib/*"  edu.stanford.nlp.ie.crf.CRFClassifier -prop austen.prop

