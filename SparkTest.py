#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pyspark import SparkConf
from pyspark import SparkContext


def map_function(x):
    """
    개별 excutor 에서 실행되는 작업
    """
    manager = global_manager.value

    # 형태소 및 개체명 인식기 사전 오픈
    manager.util.open_pos_tagger()
    manager.util.open_sp_project_ner()

    line = x.strip()
    if line == '':
        return line

    result = line
    try:
        result = manager.spark_batch(line)
    except Exception:
        pass

    return result


if __name__ == "__main__":
    """
    """
    conf = SparkConf()

    conf.setMaster('yarn-client')
    conf.setAppName('spark-nltk')

#    conf.set("spark.hadoop.mapred.input.compress", "true")
#    conf.set("spark.hadoop.mapred.input.compression.codec", "true")
#    conf.set("spark.hadoop.mapred.input.compression.codec", "org.apache.hadoop.io.compress.BZip2Codec")

#    conf.set("spark.hadoop.mapred.output.compress", "true")
#    conf.set("spark.hadoop.mapred.output.compression.codec", "true")
#    conf.set("spark.hadoop.mapred.output.compression.codec", "org.apache.hadoop.io.compress.BZip2Codec")
#    conf.set("spark.hadoop.mapred.output.compression.type", "BLOCK")

    sc = SparkContext(conf=conf)

    # 전처리 모듈에서 사용되는 파일을 실행되는 위치로 다운로드
    sc.addFile('hdfs:///user/root/src/_NCKmat.so')
    sc.addFile('hdfs:///user/root/src/_NCSPProject.so')
    sc.addFile('hdfs:///user/root/src/sp_config.ini')

    sc.addPyFile('hdfs:///user/root/src/NCKmat.py')
    sc.addPyFile('hdfs:///user/root/src/NCSPProject.py')
    sc.addPyFile('hdfs:///user/root/src/NCPreProcess.py')
    sc.addPyFile('hdfs:///user/root/src/NCCrawlerUtil.py')
    sc.addPyFile('hdfs:///user/root/src/NCNlpUtil.py')
    sc.addPyFile('hdfs:///user/root/src/NCHtmlParser.py')
    sc.addPyFile('hdfs:///user/root/src/NCNewsKeywords.py')

    # 사전 초기화
    from NCNlpUtil import NCNlpUtil
    from NCPreProcess import NCPreProcess
    from NCNewsKeywords import NCNewsKeywords

    manager = NCPreProcess()
    manager.util = NCNlpUtil()

#    manager.keywords_extractor = NCNewsKeywords()
#    manager.keywords_extractor.load_dictionary()

    global_manager = sc.broadcast(manager)

    # 입력 문서 파일을 로딩해서 각 worker 노드에 분산 저장
    lines  = sc.textFile('data/nate_baseball.500k.json.bz2')

    # map 실행
    result = lines.map(map_function)

    # 결과 저장
    result.saveAsTextFile('result', compressionCodecClass="org.apache.hadoop.io.compress.BZip2Codec")

    global_manager.unpersist()
    global_manager.destroy()

    sc.stop()


# http://spark.apache.org/docs/latest/running-on-yarn.html

