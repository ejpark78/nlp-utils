#!/bin/bash


# get script path & directory path
real_fname=$(realpath "$0")
base_dir=$(dirname "$real_fname")

# include library
source "$base_dir/smi.sh"

# main
max_part=12
schema="smi"

db_out="$1"
db_a="$2"
db_b="$3"

# check arguments
if [[ ! -f "$db_a" ]] || [[ ! -f "$db_b" ]] ; then
  echo "Uage: "$(basename $0)" <out db file name> <a db file name> <b db file name>"
  exit 1
fi

# check file size
size_a=$(du -k "$db_a" | cut -f1)
size_b=$(du -k "$db_b" | cut -f1)

# swap: 
if (( "$size_a" < "$size_b" )) ; then
  echo -e "swap '$db_a' and '$db_b', '$db_a' will be destination." 1>&2
  tmp="$db_a"
  db_a="$db_b"
  db_b="$tmp"
fi

fname=$(basename "$db_out")
fname=${fname%.*}

# split big db
header_db_out="$fname.part"

header_a=${db_a%.*}".part"
header_b=${db_b%.*}".part"

# split db to sql part
run_split_db "$db_a" "$header_a" $max_part
run_split_db "$db_b" "$header_b" $max_part

# sql part to parted db
sql_to_db "$header_db_out" "$header_a" "$header_b" $max_part "rm"

# merge db
g_list=()
init_g_list "$max_part"

binary_merge "$db_out" "$header_db_out" "$schema"

# dump file
dump_target_db "$db_out" "$schema"

