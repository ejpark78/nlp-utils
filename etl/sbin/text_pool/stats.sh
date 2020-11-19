#!/usr/bin/env bash

in=$1
out=$2
count=$3

echo -ne "전체 수량\t" | tee ${count}
pbzip2 -c -d ${in} | wc -l | tee -a ${count}

pbzip2 -c -d ${in} | jq .named_entity_v2 | grep -P ":리니지m_|:게임공통_" | pbzip2 > ${out}
sync

echo -ne "태깅 수량\n" | tee -a ${count}
echo -ne "\n게임공통\t" | tee -a ${count}
pbzip2 -c -d ${out} | grep ":게임공통_" | wc -l | tee -a ${count}

echo -ne "\n리니지m\t" | tee -a ${count}
pbzip2 -c -d ${out} | grep ":리니지m_" | wc -l | tee -a ${count}

echo -ne "\n\n태그별 수량:\n" | tee -a ${count}
pbzip2 -c -d ${out} \
    | perl -ple 's/(<[^<]+?:[^ ]+?>)/\n$1\n/g' \
    | grep -P '^<' | grep -P '>$' \
    | LC_ALL=C sort | LC_ALL=C uniq -c | LC_ALL=C sort -n -r \
    | perl -ple 's/[:<>]/\t/g' \
    >> ${count}

head -n100 ${count}
