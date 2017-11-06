#!/usr/bin/env bash

work_dir="data/daum_3mins_baseball"
mkdir -p ${work_dir}

year=2015
mongoexport --host gollum01 --db daum_3min_baseball --collection ${year} \
    | python3 NCPreProcess.py -convert_3mins \
    | gzip - > "${work_dir}/${year}.text.gz"

zcat "${work_dir}/${year}.text.gz" \
    | python3 NCPreProcess.py -extract_sentence_3mins \
    | LC_COLLATE="C" sort -u \
    | gzip - > "${work_dir}/${year}.unique_sentence.gz"

zcat "${work_dir}/${year}.unique_sentence.gz" \
    | python3 NCPreProcess.py -preprocess \
    | gzip - > "${work_dir}/${year}.pos_tagged.gz"

zcat "${work_dir}/${year}.pos_tagged.gz" \
    | java -Xms1g -Xmx1g -jar "parser/parser.jar" "parser/model/" \
    | gzip - > "${work_dir}/${year}.pre_processed.gz"

zcat "${work_dir}/${year}.pre_processed.gz" \
    | python3 NCPreProcess.py -make_sentence_index -index_file_name "${work_dir}/${year}.sqlite3"

zcat "${work_dir}/${year}.text.gz" \
    | python3 NCPreProcess.py -merge_result_3mins -index_file_name "${work_dir}/${year}.sqlite3" \
    | gzip - > "${work_dir}/${year}.text_pre_processed.gz"

zcat "${work_dir}/${year}.text_pre_processed.gz" \
    | mongoimport --host gollum02 --db daum_3mins_baseball --collection ${year}


#description_pos_tagged : [
#"도태훈 선수는 1군이 너무 떨렸나요.",
#"유격수 실책에 이어 박석민 실책까지.",
#"행운의 득점과 김태균의 적시타로 앞서가는 한화!",
#"어쨌든 부상 안 당하는게 제일 중요할텐데요ㅠㅠ"
#]
#
#description_d_parsered : [
#"도태훈 선수는 1군이 너무 떨렸나요.",
#"유격수 실책에 이어 박석민 실책까지.",
#"행운의 득점과 김태균의 적시타로 앞서가는 한화!",
#"어쨌든 부상 안 당하는게 제일 중요할텐데요ㅠㅠ"
#]
