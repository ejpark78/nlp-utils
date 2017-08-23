#!/usr/bin/env bash

export GIT_SSL_NO_VERIFY=1

git config --global user.email "ejpark@ncsoft.com"
git config --global user.name "박은진"

git config credential.helper store
git config --global http.sslverify false

