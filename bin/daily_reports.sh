#!/usr/bin/env bash

#jupyter nbconvert --to notebook --inplace --execute notebook/daily_report.ipynb

jupyter nbconvert --to html --execute notebook/daily_report.ipynb --output reports.html --output-dir .
jupyter nbconvert --to webpdf --execute notebook/daily_report.ipynb --output reports --output-dir .

python3 crawler/utils/smtp_rely.py \
  --server "172.20.0.116" \
  --from "ejpark@ncsoft.com" \
  --to "ejpark@ncsoft.com,jaehyunpark@ncsoft.com,gunyoung20@ncsoft.com,kimgihwan@ncsoft.com" \
  --contents "./reports.html" \
  --attach "./reports.pdf"
