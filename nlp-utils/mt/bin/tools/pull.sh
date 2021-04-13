#!/bin/bash


server="$1"
extra_opt="$2"

client=$(hostname)

path="$PWD"

if [ "$server" == "" ]; then
  server="ejnas"
fi

echo -e "pull '$client' <- '$server', path: '$path', extra_opt: '$extra_opt'\n\n" 1>&2

ssh -T -oStrictHostKeyChecking=no "$server" <<EOF
if [[ ! -d "$path" ]] ; then
  mkdir -p "$path"
  sync
fi
exit
EOF
sync

rsync -avz $extra_opt --progress $server:"$path/" "$path/"
sync

