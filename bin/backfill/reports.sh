#!/usr/bin/env bash

today=$(date "+%Y-%m-%d_%H%M%S")

notebook="notebook/backfill-state.ipynb"
output_prefix="backfill-${today}"
output_dir="data/reports"

mail_to="ejpark@ncsoft.com,jaehyunpark@ncsoft.com,gunyoung20@ncsoft.com,kimgihwan@ncsoft.com"
#mail_to="ejpark@ncsoft.com"
mail_from="ejpark@ncsoft.com"

rely_url="172.20.0.116"

mkdir -p "${output_dir}"

jupyter nbconvert --to notebook --execute "${notebook}" --output-dir "${output_dir}" --output "${output_prefix}"

jupyter nbconvert --to html --execute "${notebook}" --output-dir "${output_dir}" --output "${output_prefix}.html"
jupyter nbconvert --to webpdf --execute "${notebook}" --output-dir "${output_dir}" --output "${output_prefix}"

#subject="[Backfill State] "$(date "+%Y-%m-%d %H:%M:%S")
subject="[Backfill State] Range: 2021-01-01~2021-03-22"
echo "mail to: ${mail_to}, subject: ${subject}"

python3 crawler/utils/smtp_rely.py \
  --server "${rely_url}" \
  --from "${mail_from}" \
  --to "${mail_to}" \
  --subject "${subject}" \
  --contents "${output_dir}/${output_prefix}.html" \
  --attach "${output_dir}/${output_prefix}.pdf,${output_dir}/${output_prefix}.ipynb"
