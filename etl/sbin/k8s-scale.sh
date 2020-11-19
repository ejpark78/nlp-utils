#!/usr/bin/env bash

kubectl delete -f kmat
kubectl delete -f ner
kubectl delete -f nluwrapper
kubectl delete -f sbd

# restart
kubectl delete -f kmat && kubectl apply -f kmat
kubectl delete -f ner && kubectl apply -f ner
kubectl delete -f nluwrapper && kubectl apply -f nluwrapper
kubectl delete -f sbd && kubectl apply -f sbd


kubectl apply -f kmat
kubectl apply -f ner
kubectl apply -f nluwrapper
kubectl apply -f sbd

kubectl get -n nlu-wrapper all


# autoscale
kubectl -n nlu-wrapper autoscale deployment deploy-kmat-economy --min=1 --max=50
kubectl -n nlu-wrapper autoscale deployment deploy-kmat-baseball --min=1 --max=50
kubectl -n nlu-wrapper autoscale deployment deploy-ner-economy --min=1 --max=50
kubectl -n nlu-wrapper autoscale deployment deploy-ner-baseball --min=1 --max=50
kubectl -n nlu-wrapper autoscale deployment deploy-sbd-literary --min=1 --max=50
kubectl -n nlu-wrapper autoscale deployment deploy-nluwrapper --min=1 --max=30

kubectl -n corpus-pipline autoscale deployment deploy-corpus-pipline --min=1 --max=30

# scale in
kubectl -n nlu-wrapper scale deployment deploy-kmat-baseball --replicas=3
kubectl -n nlu-wrapper scale deployment deploy-ner-baseball --replicas=3

kubectl -n nlu-wrapper scale deployment deploy-kmat-economy --replicas=3
kubectl -n nlu-wrapper scale deployment deploy-ner-economy --replicas=3
kubectl -n nlu-wrapper scale deployment deploy-sbd-literary --replicas=3
kubectl -n nlu-wrapper scale deployment deploy-nluwrapper --replicas=3

kubectl -n corpus-pipline scale deployment deploy-corpus-pipline --replicas=3

# scale out
kubectl -n nlu-wrapper scale deployment deploy-kmat-baseball --replicas=50
kubectl -n nlu-wrapper scale deployment deploy-ner-baseball --replicas=50

kubectl -n nlu-wrapper scale deployment deploy-kmat-economy --replicas=50
kubectl -n nlu-wrapper scale deployment deploy-ner-economy --replicas=50
kubectl -n nlu-wrapper scale deployment deploy-sbd-literary --replicas=50
kubectl -n nlu-wrapper scale deployment deploy-nluwrapper --replicas=30

kubectl -n corpus-pipline scale deployment deploy-corpus-pipline --replicas=20

