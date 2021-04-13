#!/bin/bash

t=$(uchardet "$1")

if [[ $t == *"unknown" ]] ; then
  t=${t/\/unknown//}
fi

iconv -c -f $t -t utf8 "$1"
