#!/usr/bin/env bash

kubectl delete -f $1 && kubectl apply -f $1

# kubectl delete -f naver.yaml && kubectl apply -f naver.yaml
#kubectl delete -f nate.yaml && kubectl apply -f nate.yaml
#kubectl delete -f daum.yaml && kubectl apply -f daum.yaml

kubectl get -n crawler all 
