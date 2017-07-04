#!/usr/bin/env bash

max_map_count="$1"

input_filename="$2"
output_filename="$3"

mapper_cmd="$4"
reducer_cmd="$5"

update_dictionary="$6"

# 입력 파라메터 확인
if [ "${mapper_cmd}" == "" ] || [ "${input_filename}" == "" ] || [ "${output_filename}" == "" ] ; then
    echo "Usage: "$(basename $0)" [max map count] [입력 파일명] [결과 파일명] [mapper] [reducer] [update dictionary]"
    exit 1
fi

# 경로 설정
export PATH=${HADOOP_HOME}/bin:${SPARK_HOME}/bin:.:$PATH
env

# 파일 경로 및 파일명 분리
f_base=$(basename ${input_filename})
f_dir=$(dirname ${input_filename})

# 확장자 제거
f_name=${f_base%.*}

home="hdfs://master:9000/user/root"

# 최대 map task 수
max_reduce_count=0
error_ratio=10

if [[ "${reducer_cmd}" != "" ]] ; then
    max_reduce_count=10
fi

# 결과 저장 경로
output_dir="${home}/${f_dir}/${f_name}.result"

# 파일 업로드
echo -e "\n입력 파일 업로드: ${input_filename} to ${home}/${f_dir}/"
hdfs dfs -mkdir -p ${home}/${f_dir}

hdfs dfs -rm -f -skipTrash "${home}/${f_dir}/${f_base}"
time hdfs dfs -put ${input_filename} ${home}/${f_dir}/

# 사전 압축 및 업로드
if [[ "${update_dictionary}" != "" ]] ; then
    echo -e "\n사전 압축 및 업로드: ${home}/dictionary.jar"
    jar cvf dictionary.jar -C dictionary/ .
    hdfs dfs -rm -skipTrash "${home}/dictionary.jar"
    hdfs dfs -put dictionary.jar ${home}/
fi

# 결과 폴더 삭제
echo -e "\n결과 폴더 삭제 및 생성: ${output_dir}"
hdfs dfs -mkdir -p ${output_dir}
hdfs dfs -rm -r -f -skipTrash ${output_dir}

echo -e "\n하둡 스트리밍 실행: ${f_dir}/${f_base}, max_map_count: ${max_map_count}"
# golum
jar_file="$HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-2.8.0.jar"

time yarn jar ${jar_file} \
    -archives "${home}/dictionary.jar#dictionary" \
    -files src,parser \
    -D mapred.input.compress=true \
    -D mapreduce.output.fileoutputformat.compress=true \
    -D mapreduce.output.fileoutputformat.compress.codec=org.apache.hadoop.io.compress.BZip2Codec \
    -D mapreduce.job.name="hadoop streaming" \
    -D mapreduce.job.maps=${max_map_count} \
    -D mapreduce.job.reduces=${max_reduce_count} \
    -D mapreduce.map.failures.maxpercent=${error_ratio} \
    -D mapreduce.reduce.failures.maxpercent=${error_ratio} \
    -cmdenv "LC_COLLATE=C" \
    -input "${f_dir}/${f_base}" \
    -output "${output_dir}" \
    -mapper "${mapper_cmd}" \
    -reducer "${reducer_cmd}"

echo -e "\n결과 파일 다운로드: ${output_filename}"
time hdfs dfs -cat ${output_dir}/part-*.bz2 > "${output_filename}"

echo -e "\n결과 폴더 삭제: ${output_filename}"
time hdfs dfs -rm -r -f -skipTrash ${output_dir}

echo -e "\n입력 파일 삭제: ${home}/${f_dir}/${f_base}"
time hdfs dfs -rm -r -f -skipTrash ${home}/${f_dir}/${f_base}
