#!/bin/bash

pip3 install --upgrade \
    notebook   \
    hide_code  \
    matplotlib \
    plotly     \
    pandas     \
    numpy      \
    pymysql    \
    sqlalchemy \
    boto       \
    tensorflow \
    scipy      \
    scikit-learn \
    statsmodels  \
    sympy

jupyter nbextension install --py hide_code
jupyter nbextension enable --py hide_code
jupyter serverextension enable --py hide_code


pip3 install https://dist.apache.org/repos/dist/dev/incubator/toree/0.2.0/snapshots/dev1/toree-pip/toree-0.2.0.dev1.tar.gz
jupyter toree install         \
    --spark_home=${SPARK_HOME}    \
    --spark_opts='--master=yarn'  \
    --kernel_name=scala           \
    --interpreters=Scala

mv /usr/local/share/jupyter/kernels/scala_scala /usr/local/share/jupyter/kernels/scala



cp /data/nlp_home/ejpark/.jupyter/kernels/pyspark/kernel.json /usr/local/share/jupyter/kernels/pyspark/kernel.json
cp /data/nlp_home/ejpark/.jupyter/kernels/scala/kernel.json /usr/local/share/jupyter/kernels/scala/kernel.json


jupyter notebook --ip=0.0.0.0 --port=8000 --notebook-dir=$HOME

