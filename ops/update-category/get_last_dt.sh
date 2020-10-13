#!/usr/bin/env bash

kubectl get po | grep -v NAME | cut -f1 -d' ' | tee index

kubectl get po | grep -v NAME | cut -f1 -d' ' \
  | xargs -I{} echo "kubectl logs --tail=20 po/{} | grep ^{ | grep MESSAGE | head -n 1 | jq -r .date" \
  | sh - | tee dt

kubectl get po | grep -v NAME | cut -f1 -d' ' \
  | xargs -I{} echo "kubectl logs --tail=20 po/{} | grep ^{ | grep MESSAGE | head -n 1 | jq -r .category" \
  | sh - | tee category

wc -l index dt category
paste index category dt | tee last-date.txt

rm index dt category
