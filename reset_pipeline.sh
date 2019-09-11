#!/usr/bin/env bash

# scale in
kubectl -n nlu-wrapper scale deployment deploy-kmat-baseball --replicas=1
kubectl -n nlu-wrapper scale deployment deploy-ner-baseball --replicas=1

kubectl -n nlu-wrapper scale deployment deploy-kmat-economy --replicas=1
kubectl -n nlu-wrapper scale deployment deploy-ner-economy --replicas=1
kubectl -n nlu-wrapper scale deployment deploy-sbd-literary --replicas=1
kubectl -n nlu-wrapper scale deployment deploy-nluwrapper --replicas=1

kubectl -n corpus-pipline scale deployment deploy-corpus-pipline --replicas=1

sleep 10

# scale out
kubectl -n nlu-wrapper scale deployment deploy-kmat-baseball --replicas=50
kubectl -n nlu-wrapper scale deployment deploy-ner-baseball --replicas=50

kubectl -n nlu-wrapper scale deployment deploy-kmat-economy --replicas=50
kubectl -n nlu-wrapper scale deployment deploy-ner-economy --replicas=50
kubectl -n nlu-wrapper scale deployment deploy-sbd-literary --replicas=50
kubectl -n nlu-wrapper scale deployment deploy-nluwrapper --replicas=30

kubectl -n corpus-pipline scale deployment deploy-corpus-pipline --replicas=20

sleep 10
