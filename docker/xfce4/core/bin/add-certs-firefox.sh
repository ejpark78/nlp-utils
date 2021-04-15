#!/usr/bin/env bash

firefox &
sleep 5

add-certs.sh /usr/share/ca-certificates/SSLVACERT.crt ncsoft
add-certs.sh /usr/share/ca-certificates/SSLVACERT_ECC.crt ncsoft_ecc
