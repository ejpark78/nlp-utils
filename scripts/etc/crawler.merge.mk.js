use mk_english_tech;

var year = '2016';
var docs = db.getCollection(year).find({});

use mk_english;
docs.forEach(function(doc){
    doc['section'] = "tech";
    db.getCollection(year).save(doc);
});







use crawler;

var docs = db.getCollection('schedule').find({'group': 'chosun_daemon'});

docs.forEach(function(doc){
    db.getCollection('to_do').save(doc);
});


db.getCollection('schedule').remove({'group': 'chosun_daemon'});
