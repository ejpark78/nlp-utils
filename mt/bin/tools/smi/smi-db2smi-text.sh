#!/bin/bash


# get script path & directory path
real_fname=$(realpath "$0")
base_dir=$(dirname "$real_fname")

# include library
source "$base_dir/smi.sh"

# main
max_core=12
schema="smi_text"

fname_db="$1"

# check arguments
if [[ "$fname_db" == "" ]] || [[ ! -f "$fname_db" ]] ; then
  echo "Uage: "$(basename "$0")" <db file name>"
  exit 1
fi

# make output db name.
ext=${fname_db##*.}
fname=$(basename $fname_db .$ext)
    
fname_out="$fname.smi_text.db"

echo -e "fname_db: $fname_db, fname_out: $fname_out"

# check fname out exists
if [ -f "$fname_out" ] ; then
  echo -e "'$fname_out' is exists. '$fname_out' will be delete."
  rm "$fname_out" && sync
fi


# smi-db to unique text
header="$fname.smi_text.part"
smidb2text "$header"

# merge db
g_list=()
init_g_list "$max_core"
binary_merge "$fname_out" "$header" "$schema"

# db to text
sqlite3 "$fname_out" "SELECT smi_text FROM smi_text" | cut -f2- > "$fname.uniq.txt"

# dump file
dump_target_db "$fname_out" "$schema"
