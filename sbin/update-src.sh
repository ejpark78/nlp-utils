#!/usr/bin/env bash

for filename in $(ls ../*.py) ; do
    fname=$(basename ${filename})

    if [ -f ${fname} ] ; then
        continue
    fi

    echo ${filename} ${fname}
    ln -s ${filename} ${fname}
done