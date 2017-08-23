#!/usr/bin/env bash

# 2016년 10월 21일: 플레이오프 1차전
# 2016년 10월 29일: 한국시리즈 1차전


# 2016년 10월 3일: 김태균(한화) 통산 300출루 달성

start_date="2016-10-03"
end_date="2016-10-03"

mongoexport --host gollum02 --db baseball_nate --collection 2016 --query '{
    "date": {
        $gte: {$date: "'${start_date}'T00:00:00.000Z"},
        $lte: {$date: "'${end_date}'T23:59:59.999Z"}
    }
}' | bzip2 - > nate_baseball.${start_date}~${end_date}.json.gz





# 2016년 9월 29일: 테임즈(NC) 음주운전 사건

start_date="2016-09-29"
end_date="2016-09-29"

mongoexport --host gollum02 --db baseball_nate --collection 2016 --query '{
    "date": {
        $gte: {$date: "'${start_date}'T00:00:00.000Z"},
        $lte: {$date: "'${end_date}'T23:59:59.999Z"}
    }
}' | bzip2 - > nate_baseball.${start_date}~${end_date}.json.gz







host="gollum01"
db_name="nate_baseball"
collection="2016"

start_date="2016-01-01"
end_date="2016-08-01"

mongoexport --host ${host} --db ${db_name} --collection ${collection} --query '
{
    "date": {
        $gte: {$date: "'${start_date}'T00:00:00.000Z"},
        $lte: {$date: "'${end_date}'T00:00:00.000Z"}
    }
}' | gzip - > ${host}.${db_name}.${collection}.${start_date}~${end_date}.json.gz





#    "date": {
#        $gte: {$date: "2014-07-04T00:00:00.000Z"},
#        $lte: {$date: "2014-07-06T00:00:00.000Z"}
#    }



host="gollum"
db_name="nate_baseball"
collection="2016"
zcat gollum01.nate_baseball.2016.2016-01-01~2016-08-01.json.result.gz | mongoimport --host ${host} --db ${db_name} --collection ${collection}


