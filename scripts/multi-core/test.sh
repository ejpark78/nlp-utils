#!/usr/bin/env bash

max_line=100000

script_path="./scripts/multi-core"

# export LANGUAGE=en_US.UTF-8
# export LANG=en_US.UTF-8
# export LC_ALL=en_US.UTF-8
# update-locale LANG=en_US.UTF-8

${script_path}/multi.sh "extract_text" "data/nate/text.2012.bz2" "data/nate/2012.text.bz2" $(nproc) && sync

${script_path}/multi.sh "extract_sentence" "data/nate/2012.text.bz2" "data/nate/2012.sentence.json.bz2" $(nproc) && sync

bzcat "data/nate/2012.sentence.json.bz2" | python3 NCCorpus.py -get_json_value -key sentence | LC_COLLATE="C" sort -S 50% --parallel=$(nproc) | uniq -c | bzip2 - > "data/nate/2012.sentence.text.bz2"


bzcat data/nate/2012.sentence.text.bz2 | perl -nle '($f, $b)=split(/\t/, $_); print if $f > 10;' | grep 기자


cat test.json | python3 NCPreProcess.py -extract_text | pretty.py


str_header="

([곽소영 기자 muzpill@mydaily.co.kr])
([정리 = 곽소영 기자 muzpill@mydaily.co.kr])
(KBS 화면 캡쳐)  News1 이동원 기자
(KBS 화면 캡쳐)  News1 이동원 기자
(SBS ESPN 정진구 기자)
(SBS 통합온라인뉴스센터 정진구 기자)
(YTN 캡처)
(가고시마=스포츠코리아)
(경사=스포츠코리아)
(경산=연합뉴스) 이재혁 기자 =
(고양=뉴스1) 이동원 기자
(고양=스포츠코리아)
(고양=연합뉴스) 임병식 기자 =
(광주=스포츠코리아)
(권현진 기자/news@isportskorea.com 사진_롯데자이언츠)
(기노완=연합뉴스) 이지은 기자 =
관/련/기/사

"


str_tail="
(김재현 기자/news@isportskorea.com)
(김종원 기자/news@isportskorea.com)
(박화용 기자/news@isportskorea.com)
/ 김용일 기자
/ 박성일기자 sungil@sportsseoul.com
2012.11.5
2012.2.19
2012.3.6
2012.6.12/뉴스1
강영조기자 kanjo@sportsseoul.com
김경민 기자 kyungmin@sportschosun.com / 2012.06.09.
배우근기자 kenny@sportsseoul.com
이주상기자.rainbow@sportsseoul.com
정재근 기자 cjg@sportschosun.com
허상욱 기자 wook@sportschosun.com/2012.12.10
(문학=김진성 기자 kkomag@mydaily.co.kr)

"