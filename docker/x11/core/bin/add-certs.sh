#!/usr/bin/env bash

function usage {
  echo "Error: no certificate filename or name supplied."
  echo "Usage: $ ./add-certs.sh <certname>.pem <Cert-DB-Name>"
  exit 1

}

if [ -z "$1" ] || [ -z "$2" ]
  then
    usage
fi

certificate_file="$1"
certificate_name="firefox"

for certDB in $(find  ~/.mozilla* -name "cert9.db"); do
  cert_dir=$(dirname ${certDB});

  echo "Mozilla Firefox certificate" "install '${certificate_name}' in ${cert_dir}"
  certutil -A -n "${certificate_name}" -t "TCu,Cuw,Tuw" -i ${certificate_file} -d sql:"${cert_dir}"
done
