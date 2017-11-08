#!/usr/bin/env bash

home=$PWD

for filename in $(ls ../*.py ../*.ini) ; do
    fname=$(basename ${filename})

    if [ -f ${fname} ] ; then
        continue
    fi

    echo ${filename} ${fname}
    cp ${filename} ${fname}
done

for sub_dir in crawler language_utils ; do
    mkdir ${sub_dir}
    cd ${sub_dir}
    for filename in $(ls ../../${sub_dir}/*.py) ; do
        fname=$(basename ${filename})

        if [ -f ${fname} ] ; then
            continue
        fi

        echo ${filename} ${fname}
        cp ${filename} ${fname}
    done

    cd ${home}
done

cd language_utils
home=$PWD

for sub_dir in crf sp_utils ; do
    mkdir ${sub_dir}
    cd ${sub_dir}
    for filename in $(ls ../../../language_utils/${sub_dir}/*.py ../../../language_utils/${sub_dir}/*.so) ; do
        fname=$(basename ${filename})

        if [ -f ${fname} ] ; then
            continue
        fi

        echo ${filename} ${fname}
        cp ${filename} ${fname}
    done

    cd ${home}
done
