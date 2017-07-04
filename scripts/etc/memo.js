db.adminCommand({"setParameter": 1, "internalQueryExecMaxBlockingSortBytes": 134217728});



var query={"date": {$type: "string"}};
db.getCollection('2017').find(query);




// 문자열로된 날짜를 날짜로 변경
var collection="2016";
var query={"date": {$type: "string"}};

db.getCollection(collection).find(query).forEach(function (element) {
    element.date = ISODate(element.date);
    if (element.section === "") {
        delete element.section;
    }
    db.getCollection(collection).save(element);
});




db.getCollection("2017").find({
    "date": {
        "$gt": ISODate("2017-06-10T00:00:00Z"),
        "$lt": ISODate("2017-06-15T00:00:00Z")
    }
});


db.getCollection("2017").find({
    "date": {
        "$gt": ISODate("2017-06-15T00:00:00Z")
    }
}).sort({"date": -1});



