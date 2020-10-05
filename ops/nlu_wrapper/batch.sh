

docker pull galadriel02.korea.ncsoft.corp:5000/dependency-parser:latest
docker pull galadriel02.korea.ncsoft.corp:5000/kmat:latest
docker pull galadriel02.korea.ncsoft.corp:5000/nctime-2018:latest
docker pull galadriel02.korea.ncsoft.corp:5000/ner-rule-2018:latest
docker pull galadriel02.korea.ncsoft.corp:5000/nlu_wrapper:latest
docker pull galadriel02.korea.ncsoft.corp:5000/sbd_crf:latest


docker tag galadriel02.korea.ncsoft.corp:5000/dependency-parser:latest registry.nlp-utils/dependency-parser:latest
docker tag galadriel02.korea.ncsoft.corp:5000/kmat:latest registry.nlp-utils/kmat:latest
docker tag galadriel02.korea.ncsoft.corp:5000/nctime-2018:latest registry.nlp-utils/nctime-2018:latest
docker tag galadriel02.korea.ncsoft.corp:5000/ner-rule-2018:latest registry.nlp-utils/ner-rule-2018:latest
docker tag galadriel02.korea.ncsoft.corp:5000/nlu_wrapper:latest registry.nlp-utils/nlu_wrapper:latest
docker tag galadriel02.korea.ncsoft.corp:5000/sbd_crf:latest registry.nlp-utils/sbd_crf:latest
