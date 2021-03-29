
# NLU Wrapper

## docker image 등록 

```bash

prefix_from="galadriel02.korea.ncsoft.corp:5000"
prefix_to="registry.nlp-utils/nlu-wrapper"

cat <<EOF | tee image.list
char-automatic-word-spacing:latest
dependency-parser:latest
kmat:latest
nctime-2018:latest
ner-rule-2018:latest
nlu-wrapper:latest
sbd_crf:latest
sentiment-classifier:latest
tense:latest
EOF

# pull image
cat image.list | xargs -I{} echo "docker pull ${prefix_from}/{}"

# rename image
cat image.list | sed -r 's/^.+\///' \
  | xargs -I{} echo "docker tag ${prefix_from}/{} ${prefix_to}/{}"

# push image
cat image.list | sed -r 's/^.+\///' \
  | xargs -I{} echo "docker push ${prefix_to}/{}"

# remove image 
cat image.list | xargs -I{} echo "docker rmi ${prefix_from}/{}"
cat image.list | xargs -I{} echo "docker rmi ${prefix_to}/{}"
  
```

# docker registry 이미지 목록 조회 

```bash
REGISTRY=galadriel02.korea.ncsoft.corp:5000 \
  curl -s -k -X GET "https://${REGISTRY}/v2/_catalog" | jq .


API_NAME=sbd_crf \
REGISTRY=galadriel02.korea.ncsoft.corp:5000 \
  curl -s -k -X GET "https://${REGISTRY}/v2/${API_NAME}/tags/list" | jq .


REGISTRY=galadriel02.korea.ncsoft.corp:5000 \
  curl -k -s -X GET "https://${REGISTRY}/v2/_catalog" \
    | jq '.repositories[]' \
    | grep api-center \
    | xargs -I{} curl -s -k -X GET "https://${REGISTRY}/v2/{}/tags/list"
```

## nlu wrapper 로그 확인

```bash

tail -f /project/app/common/logger/logs/*.log

```
