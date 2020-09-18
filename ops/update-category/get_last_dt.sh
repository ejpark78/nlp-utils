#!/usr/bin/env bash

kubectl get po | grep -v NAME | cut -f1 -d' ' | tee name

kubectl get po | grep -v NAME | cut -f1 -d' ' \
  | xargs -I{} echo "kubectl logs --tail=20 po/{} | grep ^{ | grep MESSAGE | head -n 1 | jq .date" \
  | sh - | tee dt

paste name dt | tee last-date.txt
rm name dt
