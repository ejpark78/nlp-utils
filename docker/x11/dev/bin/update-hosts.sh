#!/usr/bin/env bash

if [[ -f /etc/hosts.custom ]] ; then
  cat /etc/hosts.custom | sudo tee -a /etc/hosts
fi

#echo "# chrome 설정"
#sudo sed -i 's#/chrome" #/chrome" --no-sandbox #' /usr/bin/google-chrome
