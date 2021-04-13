#!/bin/bash

set -x #echo on

train_set="$1"
col_src="$2"
col_trg="$3"
src="$4"
trg="$5"
model_dir="$6"
max_memory="$7"

bin_dir=$(dirname $(realpath $0))
max_core="$(nproc)"

if [[ "${src}" == "" ]] || [[ "${trg}" == "" ]] || [[ "${train_set}" == "" ]] || [[ "${col_src}" == "" ]] || [[ "${col_trg}" == "" ]] ; then
    echo "Uage: "$(basename "$0")" [train set] [column src] [column trg] [lang src] [lang trg] [model dir]"
    echo "  ex: "$(basename "$0")" train_set.gz 2 3 ko en $""PWD/model"
    exit 1
fi

if [[ "${model_dir}" == "" ]] ; then
    model_dir="$PWD"  
fi

train_log="${model_dir}/train-log"
if [[ ! -d "${train_log}" ]] ; then
    mkdir -p "${train_log}"
    sync
fi

time {
    echo -e "model dir: '${model_dir}', src: '${src}', trg: '${trg}', train_set: '${train_set}', max_core: '${max_core}'" 1>&2

    # copy orginal train-set
    cp "${train_set}" "${train_log}/"
    sync
    
    # get clean train-set
    if [[ $(file "--mime-type" "${train_set}" | cut -d' ' -f2) == "application/gzip" ]] ; then
        zcat "${train_set}" \
            | grep -v "|" \
            | perl -nle '(@t)=split(/\t/, $_); print if( $t['$((col_src-1))'] ne "" && $t['$((col_trg-1))'] ne "" );' \
            | gzip - > "${train_set}.clean.gz"
    else 
        cat "${train_set}" \
            | grep -v "|" \
            | perl -nle '(@t)=split(/\t/, $_); print if( $t['$((col_src-1))'] ne "" && $t['$((col_trg-1))'] ne "" );' \
            | gzip - > "${train_set}.clean.gz"
    fi

    # split train set
    train_src="${model_dir}/train.${src}"
    train_trg="${model_dir}/train.${trg}"
    
    zcat "${train_set}.clean.gz" | cut -f${col_src} > "${train_src}"
    zcat "${train_set}.clean.gz" | cut -f${col_trg} > "${train_trg}"
    sync
    
    head -n10 "${train_src}" "${train_trg}" 1>&2
    wc -l "${train_src}" "${train_trg}" 1>&2
    
    # set lm type
    # lm_global="$WORKSPACE/model/lm/${trg}.lm_binary"

    lmplz="/usr/local/mosesdecoder/bin/lmplz"
    build_binary="/usr/local/mosesdecoder/bin/build_binary"

    if [[ ${max_memory} != "" ]] ; then
        ${lmplz} -o 5 -S ${max_memory} -T /tmp < "${train_trg}" > "${train_log}/${trg}.lm" || exit
    else
        ${lmplz} -o 5 -S 80% -T /tmp < "${train_trg}" > "${train_log}/${trg}.lm" || exit
    fi

    sync
    ${build_binary} "${train_log}/${trg}.lm" "${model_dir}/${trg}.lm_binary" || exit
    
    lm="${model_dir}/${trg}.lm_binary"
    sync
    
    echo -e "# train moses" 1>&2
    perl "${MOSES_SCRIPTS}/train-model.perl" \
        -first-step 1 -last-step 9 \
        -write-lexical-counts \
        -external-bin-dir "${MOSES}/bin" \
        -parallel -cores ${max_core} \
        -mgiza -mgiza-cpus ${max_core} \
        -sort-buffer-size 60G -sort-batch-size 253 \
        -sort-compress gzip -sort-parallel ${max_core} \
        -root-dir "${model_dir}" \
        -model-dir "${model_dir}" \
        -corpus "${model_dir}/train" \
        -f ${src} -e ${trg} \
        -alignment grow-diag-final-and \
        -reordering msd-bidirectional-fe \
        -lm "0:5:$lm:8" \
        |& tee "${train_log}/train-model.log"

    # extend ini
    cat "${model_dir}/moses.ini" | sed 's/\.lm_binary/.lm/' > "${model_dir}/moses.lm.ini"
    
    sync && "${bin_dir}/filter_phrase-table.sh" "${model_dir}"
    sync && "${bin_dir}/compact_phrase-table.sh" "${model_dir}"
    sync && "${bin_dir}/zip_train-log.sh" "${model_dir}"
    sync && "${bin_dir}/binary_lm2lm.sh" "${model_dir}"

    sync
}

