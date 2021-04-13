#!/bin/bash

url="$1"

if [[ "$url" == "" ]] ; then
  url="localhost"
fi

google-chrome --temp-profile "$url" >/dev/null 2>&1 &


