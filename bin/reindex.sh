#!/usr/bin/env bash

host_from="https://corpus.ncsoft.com:9200"
auth_user_from="elastic"
auth_pass_from="nlplab"

host_to="https://yonhap01:30008/_reindex?wait_for_completion=false"
auth_user_to="elastic"
auth_pass_to="languageAI12#"

args="-k -X POST -H \"Content-Type: application/json\""
to="-u ${auth_user_to}:${auth_pass_to} \"${host_to}\""

xargs -I{} echo "echo -n "{} : " && curl ${args} ${to} -d '{
  \"source\": {
    \"remote\": {
      \"host\": \"${host_from}\",
      \"username\": \"${auth_user_from}\",
      \"password\": \"${auth_pass_from}\"
    },
    \"index\": \"{}\"
  },
  \"dest\": {
    \"index\": \"{}\"
  }
}' "
