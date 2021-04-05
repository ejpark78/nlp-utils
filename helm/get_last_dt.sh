#!/usr/bin/env bash

kubectl get po | grep -v NAME | cut -f1 -d' ' | tee index

kubectl get po | grep -v NAME | perl -ple 's/\s+/\t/g' | cut -f3 | tee status

kubectl get po | grep -v NAME | cut -f1 -d' ' \
  | xargs -I{} echo "kubectl logs --tail=100 po/{} | grep ^{ | sort -r | grep MESSAGE | head -n 1 | jq -r .date" \
  | bash - | tee dt

kubectl get po | grep -v NAME | cut -f1 -d' ' \
  | xargs -I{} echo "kubectl logs --tail=100 po/{} | grep ^{ | sort -r | grep MESSAGE | head -n 1 | jq -r .category" \
  | bash - | tee category

wc -l index status dt category
paste index status category dt | tee last-date.csv

rm index status dt category
