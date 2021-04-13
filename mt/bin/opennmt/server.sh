#!/usr/bin/env bash

#!/usr/bin/env bash

set -x #echo on

user_auth=$(echo "${CONFIG_USER_AUTH}" | python3 bin/decode_jwt.py | jq -r .auth)
bin/get_config.sh "${CONFIG_HOST}" "${CONFIG_INDEX}" "${CONFIG_DOC_ID}" "${user_auth}" || exit

$( cat config.json | jq ._source.batch | jq -r 'keys[] as $k | "export \($k)=\(.[$k])"' )

export TIME="\n실행 시간: %E, 사용자: %U, 시스템: %S, CPU: %P, 전체: %e"

# 모델 다운로드
bin/time python3 bin/sync_model.py --download=true --config="${model_path}/config/sync_model.json"

onmt_server --ip 0.0.0.0 --port ${PORT} --debug --url_root ${URL_ROOT} --config ${SERVER_CONFIG}
