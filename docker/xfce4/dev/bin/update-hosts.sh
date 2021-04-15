#!/usr/bin/env bash

if [[ -f /etc/hosts.custom ]] ; then
  cat /etc/hosts.custom >> /etc/hosts
  rm /etc/hosts.custom
fi

#echo "# chrome 설정"
#sudo sed -i 's#/chrome" #/chrome" --no-sandbox #' /usr/bin/google-chrome
