
```bash

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


REGISTRY=galadriel02.korea.ncsoft.corp:5000
curl -k -X GET https://${REGISTRY}/v2/_catalog | jq .


API_NAME=sbd_crf
curl -s -k -X GET https://${REGISTRY}/v2/${API_NAME}/tags/list | jq .


curl -k -s -X GET https://${REGISTRY}/v2/_catalog \
    | jq '.repositories[]' \
    | grep api-center \
    | xargs -I{} curl -s -k -X GET https://${REGISTRY}/v2/{}/tags/list


cat <<EOS | tee img.list
sbd_crf
char-automatic-word-spacing
kmat
ner_rule_2018
dependency-parser
nctime-2018
tense
sentiment-classifier
EOS


REGISTRY=galadriel02.korea.ncsoft.corp:5000
TARGET_REG=registry.nlp-utils

cat img.list | xargs -I{} docker pull ${REGISTRY}/{}:latest

cat img.list | xargs -I{} docker tag ${REGISTRY}/{}:latest ${TARGET_REG}/nlu-wrapper/{}:latest 

cat img.list | xargs -I{} docker rmi ${TARGET_REG}/{}:latest 
cat img.list | xargs -I{} docker rmi ${REGISTRY}/{}:latest

cat img.list | xargs -I{} docker push ${TARGET_REG}/nlu-wrapper/{}:latest 

```
