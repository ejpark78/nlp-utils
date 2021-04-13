#!/usr/bin/env bash

#!/usr/bin/env bash

set -x #echo on

user_auth=$(echo "${CONFIG_USER_AUTH}" | python3 bin/decode_jwt.py | jq -r .auth)
bin/get_config.sh "${CONFIG_HOST}" "${CONFIG_INDEX}" "${CONFIG_DOC_ID}" "${user_auth}" || exit

$( cat config.json | jq ._source.batch | jq -r 'keys[] as $k | "export \($k)=\(.[$k])"' )

export TIME="\n실행 시간: %E, 사용자: %U, 시스템: %S, CPU: %P, 전체: %e"

# 코퍼스 덤프
bin/export_corpus.sh "${src}" "${trg}" "${column_src}" "${column_trg}" "${model_path}"

# Step 1: Preprocess the data
bin/time onmt_preprocess \
    -train_src "${model_path}/train.${src}" \
    -train_tgt "${model_path}/train.${trg}" \
    -save_data "${model_path}/data"
sync

# Step 2: Train the model
bin/time onmt_train \
    --gpu_ranks 0 \
    --early_stopping 4 \
    --early_stopping_criteria accuracy ppl \
    -data "${model_path}/data" \
    -save_model "${model_path}/model"
sync

# 학습 모델 업로드
bin/time python3 bin/sync_model.py --upload=true --config="${model_path}/config/sync_model.json"

# Step 3: Translate
bin/time onmt_translate \
    --gpu 0 \
    -src "${model_path}/train.${src}" \
    -output "${model_path}/train.out" \
    -model $(ls -1vr ${model_path}/model_step_*.pt | head -n1) \
    -replace_unk \
    --n_best 1 \
    --beam_size 1 \
    -verbose
sync

# step 4: evaluation
bin/time bin/parallel-evaluation.sh "${model_path}/train" "${src}" "${trg}" out

# 테스트 결과 업로드
bin/time python3 bin/sync_model.py --upload=true --config="${model_path}/config/sync_model.json"
