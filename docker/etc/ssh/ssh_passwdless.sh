#!/usr/bin/env bash

# 패스워드 없이 로그인 설정
ssh-keygen -t rsa -f /root/.ssh/id_rsa -P ''

cat /root/.ssh/id_rsa.pub >> /root/.ssh/authorized_keys

chmod 700 /root/.ssh
chmod 600 /root/.ssh/id_rsa
chmod 644 /root/.ssh/id_rsa.pub
chmod 644 /root/.ssh/authorized_keys
