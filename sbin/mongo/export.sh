#!/usr/bin/env bash

host="frodo"
port=27018
db_name="$1"

# 파라메터 확인
if [ "${db_name}" == "" ] ; then
    echo "Usage: "$(basename $0)" [db_name]"
    exit 1
fi

tool=~/sbin/mongo/mongoexport

max_count=$(nproc)

echo "목록 생성: "
declare -a collection_list=()

IFS=$'\n'
for collection in $(mongo --host ${host} --port ${port} --quiet --eval "db.getCollectionNames().join('\n');" ${db_name}) ; do
    echo "collection: "${collection}

    collection_list[${#collection_list[*]}]=${collection}
done

echo "시작: "${#collection_list[*]}", max count: "${max_count}
for (( i=0 ; i<${#collection_list[*]} ; i+=${max_count} )) ; do
    for (( j=i ; j<i+${max_count} ; j++ )) ; do
        if [[ j -ge ${#collection_list[*]} ]] ; then
            break
        fi

        collection=${collection_list[j]}
        echo ${i}, ${j}, ${collection}

        ${tool} --host ${host} --port ${port} \
            --db ${db_name} --collection ${collection} \
            | bzip2 - > ${collection}.bz2 &
    done

    echo "waiting: ~ "${i}
    wait
done

echo "년도별 병합"
for year in $(\ls ????-??.bz2 | perl -ple 's/-\d\d.bz2//;' | sort -u) ; do
    echo ${year}
    cat ${year}-??.bz2 > ${year}.bz2
    rm ${year}-??.bz2
done


#IFS=$'\n'
#for db_name in $(mongo --host ${host} --port ${port} --quiet --eval "db.getMongo().getDBNames().join('\n');") ; do
#    case ${db_name} in
#        local)
#            continue
#            ;;
#        admin)
#            continue
#            ;;
#        config)
#            continue
#            ;;
#    esac
#
#    export.sh ${db_name}
#done
