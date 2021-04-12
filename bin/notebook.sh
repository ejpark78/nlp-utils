#!/usr/bin/env bash

set -x #echo on

PORT=8888
NB_PREFIX=/
NB_TOKEN='crawler'
NB_PASSWD='crawler'

PYTHONPATH=. jupyter notebook \
  --ip='*' \
  --port=${PORT} \
  --NotebookApp.token=${NB_TOKEN} \
  --NotebookApp.password=${NB_PASSWD} \
  --NotebookApp.terminado_settings="{'shell_command': ['/bin/zsh']}" \
  --ServerApp.token=${NB_TOKEN} \
  --ServerApp.password=${NB_PASSWD} \
  --ServerApp.allow_origin='*' \
  --ServerApp.base_url=${NB_PREFIX} \
  --ServerApp.iopub_data_rate_limit=10000000
