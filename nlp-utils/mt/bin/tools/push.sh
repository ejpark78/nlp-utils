#!/bin/bash


client="$1"
extra_opt="$2"

server=$(hostname)

path="$PWD"

if [ "$client" == "" ]; then
   client="ejnas"
fi

echo -e "push '$server' -> '$client', path: '$path', extra_opt: '$extra_opt'\n\n" 1>&2

ssh -T -oStrictHostKeyChecking=no "$client" <<EOF
if [[ ! -d "$path" ]] ; then
  mkdir -p "$path"
fi
EOF
sync

rsync -avz $extra_opt --progress "$path/" $client:"$path/"
sync

