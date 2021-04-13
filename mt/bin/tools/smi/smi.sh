#!/bin/bash


#ATTACH DATABASE '""${fdb}""' AS db; 
#INSERT INTO bitext (id, filename, smi) SELECT id, filename, smi FROM db.bitext; 
#DETACH DATABASE db;"


function add_pragma {
    local fname_sql="$1"

    echo "PRAGMA legacy_file_format = 1;" >> "$fname_sql"
        
    # Turn on all the go-faster pragmas
    #echo "PRAGMA synchronous    = 0;" >> "$fname_sql"
    echo "PRAGMA temp_store     = 2;" >> "$fname_sql"
    echo "PRAGMA foreign_keys = 0;" >> "$fname_sql"
    echo "PRAGMA journal_mode = OFF;" >> "$fname_sql"
    echo "PRAGMA locking_mode = EXCLUSIVE;" >> "$fname_sql"
    
    echo "" >> "$fname_sql"
        
    sync
}


function dump_db {
    local fname_db="$1"
    local fname_sql="$2"
    local with_schema_sql="$3"
    local delete_db="$4"
    local schema="$5"
    
    echo "BEGIN TRANSACTION;" > "$fname_sql" && sync

    add_pragma "$fname_sql"
    
    if [[ "$with_schema_sql" == "with_schema" ]] ; then
        for t in $(sqlite3 "$fname_db" ".table") ; do
            sqlite3 "$fname_db" ".schema $t" >> "$fname_sql"
        done
    fi

    if [[ "$schema" == "smi_text" ]] ; then
        for t in $(sqlite3 "$fname_db" ".table") ; do
            echo -e ".mode insert $t\nSELECT * FROM $t;" \
                | sqlite3 "$fname_db" \
                >> "$fname_sql"
        done
    else
        echo -e ".mode insert smi\nSELECT smi FROM smi;" \
            | sqlite3 "$fname_db" \
            | sed 's/smi VALUES/smi (smi) VALUES/' \
            >> "$fname_sql"
            
        echo -e ".mode insert board\nSELECT * FROM board;" \
            | sqlite3 "$fname_db" \
            >> "$fname_sql"
    fi
        

    echo "COMMIT;" >> "$fname_sql"
    sync
    
    if [[ "$delete_db" == "delete_db" ]] ; then
        rm "$fname_db" && sync
    fi
}


function make_target_db {
    local fname_db="$1"
    local header="$2"
    local i="$3"
    
    c=$(printf '%02d' ${g_list[0]})
    
    echo "rename '$header.$c.db' => '$fname_db'"
    mv "$header.$c.db" "$fname_db" && sync
}


function merge_db {
    local header="$1"
    local tag_a="$2"
    local tag_b="$3"
    local schema="$4"

    tag_a=$(printf '%02d' $tag_a)
    tag_b=$(printf '%02d' $tag_b)

    # dump b
    time dump_db "$header.$tag_b.db" "$header.$tag_b.sql" "without_schema" "delete_db" "$schema"

    echo "merge: '$header.$tag_a.db' = '$header.$tag_a.db' + '$header.$tag_b.sql'"
    time sqlite3 "$header.$tag_a.db" < "$header.$tag_b.sql"
    sync

    rm "$header.$tag_b.sql" && sync
}


function binary_merge {
    local db_out="$1"
    local header="$2"
    local schema="$3"
    
    local new_list=()

    local k=0
    for (( i=0; i<"${#g_list[@]}"; i+=2 )) ; do
        j=$((i + 1))
        
        if (( "$j" < "${#g_list[@]}" )) ; then
            merge_db "$header" ${g_list[$i]} ${g_list[$j]} "$schema" &
        fi
        
        new_list[$k]=${g_list[$i]}
        k=$((k + 1))
    done
    
    wait
    echo ""
    sync

    g_list=(${new_list[@]})
    if (( "${#g_list[@]}" >= 2 )) ; then
        binary_merge "$db_out" "$header" "$schema"
    else
        make_target_db "$db_out" "$header" "${g_list[0]}"
    fi
}


function init_g_list {
    local max_core="$1"
    
    echo -e "max_core: '$max_core'" 1>&2
    
    for (( i=0 ; i<"$max_core" ; i++ )) ; do
        g_list[$i]=${i}
    done
}


function dump_target_db {
    local fname_db="$1"
    local schema="$2"
    
    local ext=${fname_db##*.}
    local fname=$(basename $fname_db .$ext)    

    time dump_db "$fname_db" "$fname.sql" "with_schema" "keep_db" "$schema"
    gzip "$fname.sql" && sync
}


function split_db {
    local fname_db="$1"
    local fname_sql="$2"
    local table_name="$3"
    local extra_query="$4"

    echo -e "db: '$fname_db', sql: '$fname_sql', table: '$table_name', total: $total, extra query: '$extra_query'" 1>&2
    
    echo "BEGIN TRANSACTION;" >> "$fname_sql" && sync

    add_pragma "$fname_sql"
    
    sqlite3 "$fname_db" ".schema $table_name" >> "$fname_sql"

    if [[ "$table_name" == "smi" ]] ; then
        echo -e ".mode insert $table_name\nSELECT smi FROM $table_name $extra_query;" \
            | sqlite3 "$fname_db" \
            | sed 's/smi VALUES/smi (smi) VALUES/' \
            >> "$fname_sql"
    else
        echo -e ".mode insert $table_name\nSELECT * FROM $table_name $extra_query;" \
            | sqlite3 "$fname_db" \
            >> "$fname_sql"
    fi

    echo "COMMIT;" >> "$fname_sql"
    sync
}


function run_split_db {
    local fname_db="$1"
    local header_sql="$2"
    local max_part="$3"

    echo -e "split db: '$fname_db' to '$header_sql'" 1>&2
 
    local table_list=$(sqlite3 "$fname_db" ".table")

    # get db total conunt
    declare -A total_list
    for table_name in ${table_list[@]} ; do
        total_list["$table_name"]=$(sqlite3 "$fname_db" "SELECT COUNT(*) FROM $table_name")
    done

    for (( i=0 ; i<$max_part ; i++ )) ; do
        local fname_sql="$header_sql."$(printf '%02d' $i)".sql"

        if [[ -f "$fname_sql" ]] ; then
            rm "$fname_sql"
        fi
    done
    sync

    for table_name in ${table_list[@]} ; do
        local total=${total_list["$table_name"]}
        local limit=$((total/max_part + 1))

        for (( i=0 ; i<$max_part ; i++ )) ; do
            local fname_sql="$header_sql."$(printf '%02d' $i)".sql"
            local offset=$((limit*i))

            split_db "$fname_db" "$fname_sql" "$table_name" "LIMIT $limit OFFSET $offset" &
        done

        wait
        sync
    done
}


function sql_to_db {
    local header_db_out="$1"
    local header_sql_a="$2"
    local header_sql_b="$3"
    local max_part="$4"
    local delete_sql="$5"

    for (( i=0 ; i<$max_part ; i++ )) ; do
        local c=$(printf '%02d' $i)
        
        local db_name="$header_db_out.$c.db"
        local sql_a="$header_sql_a.$c.sql"
        local sql_b="$header_sql_b.$c.sql"
        
        echo -e "sql to db: '$db_name' <- '$sql_a' + '$sql_b'" 1>&2
        cat "$sql_a" "$sql_b" | sqlite3 "$db_name" &
        sync
    done
    
    wait
    sync

    for (( i=0 ; i<$max_part ; i++ )) ; do
        local c=$(printf '%02d' $i)
        
        local sql_a="$header_sql_a.$c.sql"
        local sql_b="$header_sql_b.$c.sql"
        
        if [[ "$delete_sql" == "rm" ]] ; then
            rm "$sql_a" "$sql_b"
        fi
    done
    sync
}


function smi2db {
    local fname_list="$1"
    local fdb="$2"
    local board="$3"

    cat "$fname_list" \
        | perl -nle '
                s/\`/\\\`/g; 
                print "cat \"$_\" | iconv_to-utf8.sh \"$_\" | smi2db.pl -board '"${board}"' -out '"${fdb}"' -fn \"$_\""
                ' \
        | sh -
    sync
    
    rm "$fname_list"
}


function run_smi2db {
    local header="$1"
    local board="$2"
    
    # find all smi file
    find . -name "*.smi" -type f -print > "$header.list" && sync
    
    # split 12
    split.sent.sh "$header.list" $max_core "$header.list." && sync

    for (( i=0; i<$max_core; i++ )) ; do
        local c=$(printf '%02d' $i)
        local fname_list="$header.list.$c"

        local fdb="$header.$c.db"

        echo -e "fname_list: $fname_list, db: $fdb"
        time smi2db "$fname_list" "$fdb" "$board" &
    done
    
    wait
    sync
    
    rm "$header.list"
}


function smidb2text {
    local header="$1"

    for (( i=0; i<$max_core; i++ )) ; do
        c=$(printf '%02d' $i)
        if [[ -f "$header.$c.db" ]] ; then
            rm "$header.$c.db" && sync
        fi
        
        smi-db2smi-text.pl \
            -max_core $max_core \
            -db "$fname_db" \
            -i "${i}" \
            -uniq_text_db "$header.$c.db" \
            > "$header.$c.log" &
    done

    wait
    sync
}

