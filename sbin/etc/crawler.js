
// 년도별 클리닝
var start = 2006;
var end = 2017;

for( var i=start ; i<=end ; i++ ) {
    var year=i.toString();

    var count = db.getCollection(year).find({
        "$or" : [{
            "date": {"$lt": ISODate(year+"-01-01T00:00")}
        }, {
            "date": {"$gt": ISODate(year+"-12-31T24:00")}
        }]
    }).count();

    print(year, ":", count);
}

for( var i=start ; i<=end ; i++ ) {
    var year=i.toString();

    var docs = db.getCollection(year).find({
        "$or" : [{
            "date": {"$lt": ISODate(year+"-01-01T00:00")}
        }, {
            "date": {"$gt": ISODate(year+"-12-31T24:00")}
        }]
    });

    docs.forEach(function(doc){
        db.getCollection('etc').save(doc);
    });

    db.getCollection(year).remove({
        "$or" : [{
            "date": {"$lt": ISODate(year+"-01-01T00:00")}
        }, {
            "date": {"$gt": ISODate(year+"-12-31T24:00")}
        }]
    });
}



// 재분배
//var start = 2015;
//var end = 2016;

for( var i=start ; i<=end ; i++ ) {
    var year=i.toString();

    var count = db.getCollection('etc').find({
        "date": {"$gte": ISODate(year+"-01-01T00:00"), "$lte": ISODate(year+"-12-31T24:00")}
    }).count();

    print(year, ":", count);
}

//var start = 2015;
//var end = 2016;


for( var i=start ; i<=end ; i++ ) {
    var year=i.toString();

    var docs = db.getCollection('etc').find({
        "date": {"$gte": ISODate(year+"-01-01T00:00"), "$lte": ISODate(year+"-12-31T24:00")}
    });

    docs.forEach(function(doc){
        db.getCollection(year).save(doc);
    });

    db.getCollection('etc').remove({
        "date": {"$gte": ISODate(year+"-01-01T00:00"), "$lte": ISODate(year+"-12-31T24:00")}
    });
}


