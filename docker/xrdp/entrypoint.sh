#!/bin/bash

# generate xrdp key
if [ ! -f "/etc/xrdp/rsakeys.ini" ]; then
  xrdp-keygen xrdp auto
fi

# generate certificate for tls connection
if [ ! -f "/etc/xrdp/cert.pem" ]; then
  # delete eventual leftover private key
  rm -f /etc/xrdp/key.pem || true

  cd /etc/xrdp

  if [ ! $CERTIFICATE_SUBJECT ]; then
    CERTIFICATE_SUBJECT="/C=US/ST=Some State/L=Some City/O=Some Org/OU=Some Unit/CN=Terminalserver"
  fi

  openssl req -x509 -newkey rsa:2048 -nodes -keyout /etc/xrdp/key.pem -out /etc/xrdp/cert.pem -days 365 -subj "$CERTIFICATE_SUBJECT"

  crudini --set /etc/xrdp/xrdp.ini Globals security_layer tls
  crudini --set /etc/xrdp/xrdp.ini Globals certificate /etc/xrdp/cert.pem
  crudini --set /etc/xrdp/xrdp.ini Globals key_file /etc/xrdp/key.pem
fi

supervisord
