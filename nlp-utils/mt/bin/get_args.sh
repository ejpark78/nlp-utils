#!/usr/bin/env bash

#set -x #echo on

prefix=$1

declare -a opts

while IFS='=' read -r env_key env_value
do
  if [[ "${env_key}" =~ ^${prefix} ]]; then
    if [[ ! -z ${env_value} ]]; then
      name="${env_key/${prefix}/}"
      opt="--${name,,}=${env_value}"
      opts+=("${opt}")
    fi
  fi
done < <(env)

echo "${opts[@]}"
