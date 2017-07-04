
db.getCollection('schedule').update(
    {'docker.image': 'crawler:cluster'}, 
    {
        $set: {
            'docker.image': 'crawler:dev'
            }
    },
    { multi: true }
);



db.getCollection('schedule').update(
    {'parameter.domain': {$exists:false}},
    {$set: {'parameter.domain': 'economy'}},
    { multi: true });

db.getCollection('etc').update(
    {'parameter.domain': {$exists:false}},
    {$set: {'parameter.domain': 'economy'}},
    { multi: true });

db.getCollection('done').update(
    {'parameter.domain': {$exists:false}},
    {$set: {'parameter.domain': 'economy'}},
    { multi: true });
