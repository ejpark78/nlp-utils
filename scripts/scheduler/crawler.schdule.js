
var docs = db.getCollection("schedule").find({"state.state": "done"});

docs.forEach(function(doc){
    db.getCollection("done").save(doc);
});

db.getCollection("schedule").remove({"state.state": "done"});

db.getCollection("schedule").find({"state.state": "done"}).count();
