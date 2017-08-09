


// 문서 요약/분류 디비 입력

collection_name="semi_final_playoff_2014"
source_db_name="/home/ejpark/workspace/crawler/curl_result/nate.baseball/2014/2014-10.db"


collection_name="regular_season_2014"
source_db_name="/home/ejpark/workspace/crawler/curl_result/nate.baseball/2014/2014-07.db"

python3 NCPreProcess.py -insert_raw_html \
    -db_name summarization -collection "${collection_name}" \
    -host_name 172.20.78.170 -source_db_name "${source_db_name}"

// 백업

use categorization;
var docs = db.regular_season_2014.find({});

use classification;
docs.forEach( function(doc) { db.regular_season_2014.save(doc); } );


use categorization;
var docs = db.semi_final_playoff_2014.find({});

use classification;
docs.forEach( function(doc) { db.semi_final_playoff_2014.save(doc); } );





var docs = db.semi_final_playoff_2014.find({});
docs.forEach( function(doc) { db.back_up_semi_final_playoff_2014.save(doc); } );






use categorization;
var docs = db.regular_season_2014.find({});

use summarization;
docs.forEach( function(doc) { db.regular_season_2014.save(doc); } );



use summarization;
var docs = db.meta.find({});

use classification;
docs.forEach( function(doc) { db.meta.save(doc); } );




// 정규시즌
use news;
var docs = db.nate_baseball_2014.find({
    "date": {
        "$gte": ISODate("2014-07-04T00:00"),
        "$lte": ISODate("2014-07-05T24:00")
    }
});

use summarization;
docs.forEach( function(doc) { db.regular_season_2014.save(doc); } );


// 준 플레이오프
use news;
var docs = db.nate_baseball_2014.find({
    "date": {
        "$gte": ISODate("2014-10-22T00:00"),
        "$lte": ISODate("2014-10-23T24:00")
    }
});

use summarization;
docs.forEach( function(doc) { db.semi_final_playoff_2014.save(doc); } );


// 플레이오프
use news;
var docs = db.nate_baseball_2014.find({
    "date": {
        "$gte": ISODate("2014-10-27T00:00"),
        "$lte": ISODate("2014-10-28T24:00")
    }
});

use summarization;
docs.forEach( function(doc) { db.final_playoff_2014.save(doc); } );


// 한국시리즈
use news;
var docs = db.getCollection('nate_baseball_2014').find({
    "date": {
        "$gte": ISODate("2014-11-07T00:00"),
        "$lte": ISODate("2014-11-08T24:00")
    }
});

use summarization;
docs.forEach( function(doc) { db.korean_series_2014.save(doc); } );



// 통계


db.final_playoff_2014.find().count()
db.korean_series_2014.find().count()
db.regular_season_2014.find().count()
db.semi_final_playoff_2014.find().count()




db.final_playoff_2014.find({}, {title:1});



db.regular_season_2014.find({title: {$in: [/시구/]}}, {title: 1})
db.regular_season_2014.find({title: {$in: [/종합/]}}, {title: 1})

db.semi_final_playoff_2014.find({title: {$in: [/치어리더/]}}, {title: 1})


db.final_playoff_2014.find({title: {$in: [/MLB/]}}, {title: 1}).count()
db.korean_series_2014.find({title: {$in: [/MLB/]}}, {title: 1}).count()
db.regular_season_2014.find({title: {$in: [/MLB/]}}, {title: 1}).count()
db.semi_final_playoff_2014.find({title: {$in: [/MLB/]}}, {title: 1}).count()



db.regular_season_2014.remove({title: {$in: [/시구/]}})
db.regular_season_2014.remove({title: {$in: [/치어리더/]}})


// 키워드 필터링

db.semi_final_playoff_2014.find({title: {$in: [/치어리더/]}}).count()

// 14

db.semi_final_playoff_2014.remove({title: {$in: [/치어리더/]}})


db.semi_final_playoff_2014.find(
    {text_content: {$nin: [/NC/, /엔씨/, /LG/, /두산/, /한화/, /삼성/, /KIA/, /롯데/, /SK/, /넥센/]}},
    {title:1, text_content: 1}
).count()

// 64

db.semi_final_playoff_2014.remove(
    {text_content: {$nin: [/NC/, /엔씨/, /LG/, /두산/, /한화/, /삼성/, /KIA/, /롯데/, /SK/, /넥센/]}},
    {title:1, text_content: 1}
)


2335

db.semi_final_playoff_2014.find(
    {keyword: {$nin: [/NC/, /엔씨/, /LG/, /두산/, /한화/, /삼성/, /KIA/, /롯데/, /SK/, /넥센/]}},
    {title:1, text_content: 1}
).count()

70



db.regular_season_2014.find({
    "paragraph": {
        $elemMatch : {
            $elemMatch : {
                "sentence": {$in: [/치어/]}
            }
        }
    }
}).count()



db.regular_season_2014.remove({
    "paragraph": {
        $elemMatch : {
            $elemMatch : {
                "sentence": {$in: [/치어/]}
            }
        }
    }
})




//


db.korean_series_2014.remove({title: {$in: [/포토/]}})
db.final_playoff_2014.remove({title: {$in: [/포토/]}})
db.semi_final_playoff_2014.remove({title: {$in: [/포토/]}})


db.regular_season_2014.remove({title: {$in: [/MLB/]}})
db.korean_series_2014.remove({title: {$in: [/MLB/]}})
db.final_playoff_2014.remove({title: {$in: [/MLB/]}})
db.semi_final_playoff_2014.remove({title: {$in: [/MLB/]}})



db.final_playoff_2014.find().count()
db.korean_series_2014.find().count()
db.regular_season_2014.find().count()
db.semi_final_playoff_2014.find().count()



summary: [{
    ...,
}]


db.regular_season_2014.find({'summarization': {'$exists': 1}}, {"summarization": 1, "title": 1}).count()
db.regular_season_2014.find({'summarization.evaluation': {'$exists': 1}}, {"summarization": 1, "title": 1}).count()



db.adminCommand({"setParameter": 1, "internalQueryExecMaxBlockingSortBytes" : 134217728})

db.adminCommand({"getParameter": 1, "internalQueryExecMaxBlockingSortBytes" : 1})


db.jobs.find({
    "job_list.job_1": {
        $elemMatch: {name: "nate_baseball_2016_10"}
    }
})


python3 NCPreProcess.py -insert_html_content -source_db_name curl_result/nate.baseball/2005/2005-03.db -collection nate_baseball_2005
python3 NCPreProcess.py -insert_html_content -source_db_name curl_result/nate.baseball/2016/2016-08.db -collection nate_baseball_2016

for y in 2016 2015 2014 2013 2012 2011 2010 2009 2008 2007 2006 2005 ; do


section=baseball
section=economy
section=entertainment
section=it
section=society


section=tv

section=international
for y in 2016 2015 2014 2013 2012 2011 2010 2009 2008 2007 2006 2005 ; do
    for f in $(find curl_result/nate.${section}/${y}/ -name "*.db" -print) ; do
        echo ${f};
        python3 NCPreProcess.py -insert_html_content -source_db_name ${f} \
            -host_name gollum01 -port 27017 -db_name nate_${section} -collection "${y}"
    done
done




