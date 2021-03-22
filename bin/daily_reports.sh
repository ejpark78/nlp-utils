#!/usr/bin/env bash

notebook="notebook/daily_report.ipynb"
output_prefix="daily-report"
output_dir="."

mail_to="ejpark@ncsoft.com,jaehyunpark@ncsoft.com,gunyoung20@ncsoft.com,kimgihwan@ncsoft.com"
mail_from="ejpark@ncsoft.com"

rely_url="172.20.0.116"

jupyter nbconvert --to notebook --inplace --execute "${notebook}"

jupyter nbconvert --to html --execute "${notebook}" --output-dir "${output_dir}" --output "${output_prefix}.html"
jupyter nbconvert --to webpdf --execute "${notebook}" --output-dir "${output_dir}" --output "${output_prefix}"

subject="[Daily Reports] "$(date "+%Y-%m-%d %H:%M:%S")
echo "mail to: ${mail_to}, subject: ${subject}"

python3 crawler/utils/smtp_rely.py \
  --server "${rely_url}" \
  --from "${mail_from}" \
  --to "${mail_to}" \
  --subject "${subject}" \
  --contents "${output_dir}/${output_prefix}.html" \
  --attach "${output_dir}/${output_prefix}.pdf,${output_dir}/${output_prefix}.ipynb"
