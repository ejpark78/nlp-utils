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
board="$2"

# check arguments
if [[ "$fname_db" == "" ]] || [[ "$board" == "" ]] ; then
  echo "Uage: "$(basename "$0")" <db file name> <board name: gomtv cinest>"
  exit 1
fi

fname=$(basename "$fname_db")
fname=${fname%.*}

header="$fname.part"

# run smi2db with 12 core
run_smi2db "$header" "$board"

# merge db
g_list=()
init_g_list "$max_core"

binary_merge "$fname_db" "$header" "$schema"

# dump file
dump_target_db "$fname_db" "$schema"
