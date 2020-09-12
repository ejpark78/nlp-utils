#!/bin/bash
set -e

if [[ "${USER}" == "" ]] ; then
    export USER=user
fi

if [[ "${HOME}" == "" ]] || [[ "${HOME}" == "/root" ]] ; then
    export HOME=/home/${USER}
fi

if [[ "${PORT}" == "" ]] ; then
    export PORT=8888
fi

if [[ "${CONFIG}" == "" ]] ; then
    export CONFIG=${HOME}/.jupyter/jupyter_notebook_config.py
fi

token=""
if [[ "${TOKEN}" != "" ]] ; then
    token="--NotebookApp.token='${TOKEN}'"
fi

if [ -d ${HOME}/.local ]; then
  mkdir -p ${HOME}/.local
fi

cd ${HOME}/

source /etc/bash.bashrc

sudo -H -u ${USER} jupyter lab \
    --ip=0.0.0.0 \
    ${token} \
    --port=${PORT} \
    --config ${CONFIG} \
    --notebook-dir ${HOME} \
    --NotebookApp.iopub_data_rate_limit=10000000 \
    --NotebookApp.terminado_settings="{'shell_command': ['/bin/zsh']}"
