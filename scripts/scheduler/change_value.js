

db.getCollection('schedule').update({}, {$set: {"docker.network": "hadoop-net"}}, {"upsert": true, "multi": true})


