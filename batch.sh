#!/usr/bin/env bash

./reset_pipeline.sh
./corpus_pipeline_utils.sh | sh -

#./corpus_pipeline_utils.sh | parallel -j 4 -k

./reset_pipeline.sh
./corpus_pipeline_utils.sh | sh -


./reset_pipeline.sh
./corpus_pipeline_utils.sh | sh -

./reset_pipeline.sh
./corpus_pipeline_utils.sh | sh -

# scale in
kubectl -n nlu-wrapper scale deployment deploy-kmat-baseball --replicas=1
kubectl -n nlu-wrapper scale deployment deploy-ner-baseball --replicas=1

kubectl -n nlu-wrapper scale deployment deploy-kmat-economy --replicas=1
kubectl -n nlu-wrapper scale deployment deploy-ner-economy --replicas=1
kubectl -n nlu-wrapper scale deployment deploy-sbd-literary --replicas=1
kubectl -n nlu-wrapper scale deployment deploy-nluwrapper --replicas=1

kubectl -n corpus-pipline scale deployment deploy-corpus-pipline --replicas=1
