#!/usr/bin/env bash

set -x #echo on

user_auth=$(echo "${CONFIG_USER_AUTH}" | python3 bin/decode_jwt.py | jq -r .auth)
bin/get_config.sh "${CONFIG_HOST}" "${CONFIG_INDEX}" "${CONFIG_DOC_ID}" "${user_auth}" || exit

$( cat config.json | jq ._source.batch | jq -r 'keys[] as $k | "export \($k)=\(.[$k])"' )

export TIME="\n실행 시간: %E, 사용자: %U, 시스템: %S, CPU: %P, 전체: %e"

# 코퍼스 덤프
bin/time bin/export_corpus.sh "${src}" "${trg}" "${column_src}" "${column_trg}" "${model_path}" || exit

# 학습
bin/time bin/moses/train-moses.sh \
    "${model_path}/train.${src}-${trg}" \
    1 2 ${src} ${trg} \
    "${model_path}" \
    ${max_memory} \
    || exit
sync

# 학습 모델 업로드
python3 bin/sync_model.py --upload=true --config="${model_path}/config/sync_model.json"

# 자동 번역
bin/time moses --threads $(nproc) \
    -f "${model_path}/moses.binary.ini" \
    < "${model_path}/train.${src}" \
    > "${model_path}/train.out"
sync

# 자동 평가
bin/time bin/parallel-evaluation.sh "${model_path}/train" "${src}" "${trg}" out

# 테스트 결과 업로드
python3 bin/sync_model.py --upload=true --config="${model_path}/config/sync_model.json"
