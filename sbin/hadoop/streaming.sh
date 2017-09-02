#!/usr/bin/env bash

max_map_count="$1"

input_filename="$2"
output_filename="$3"

mapper_cmd="$4"
reducer_cmd="$5"

# 입력 파라메터 확인
if [ "${mapper_cmd}" == "" ] || [ "${input_filename}" == "" ] || [ "${output_filename}" == "" ] ; then
    echo "Usage: "$(basename $0)" [max map count] [입력 파일명] [결과 파일명] [mapper] [reducer]"
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

# home 경로
home="hdfs://master:9000/user/"$(id -un)

# 최대 map task 수
max_reduce_count=0
error_ratio=10

if [[ "${reducer_cmd}" != "" ]] ; then
    max_reduce_count=10
fi

# 결과 저장 경로
today=$(date +%Y%m%d)
output_dir="${f_name}.${today}"

# 권한 수정
#sudo hadoop fs -chmod -R 777 /tmp/hadoop-yarn

# 결과 폴더 삭제
echo -e "\n결과 폴더 삭제 및 생성: ${output_dir}"
hdfs dfs -mkdir -p ${output_dir}
hdfs dfs -rm -r -f -skipTrash ${output_dir}

# 하둡 스트리밍 실행
echo -e "\n하둡 스트리밍 실행: ${f_dir}/${f_base}, max_map_count: ${max_map_count}"

jar_file="${HADOOP_HOME}/share/hadoop/tools/lib/hadoop-streaming-${HADOOP_VERSION}.jar"

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
