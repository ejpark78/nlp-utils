#!/usr/bin/env bash

set -x

ipcluster nbextension enable

python3 --user -m ipykernel install
python3 --user -m bash_kernel.install
python3 --user -m sshkernel install
python3 --user -m ansible_kernel.install

echo && echo "nbextension 설치"
jupyter nbextension install --sys-prefix --py ipyparallel
jupyter contrib nbextension install
jupyter nbextensions_configurator enable

mkdir -p ~/.jupyter

echo && echo "jupyter notebook 테마 설정"
jt -t monokai -fs 11 -tfs 11 -nfs 11 -ofs 11 -cellw 980 -T -f hack -N -cellw 1280 -lineh 150

echo && echo "qgrid 설정"
jupyter nbextension enable --py --sys-prefix qgrid
jupyter nbextension enable --py --sys-prefix widgetsnbextension 

echo && echo "qgrid 설정"
ipcluster nbextension enable

echo && echo "labextension 설치"
jupyter labextension install @jupyter-widgets/jupyterlab-manager
jupyter labextension install qgrid
jupyter labextension install ipyvolume
