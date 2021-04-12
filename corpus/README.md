
# 사용법 

## docker

```bash
docker run \
		-it --rm \
		--name corpus \
		--hostname corpus \
		--network host \
		-e PORT=8889 \
		--add-host "nlp-utils:172.19.153.41" \
		--add-host "nlp-s3.cloud.ncsoft.com:172.19.153.41" \
		registry.nlp-utils/corpus:latest
```

## 설치 

```bash
pip3 install git+http://galadriel02.korea.ncsoft.corp/crawler-dev/corpus.git@dev
```

## 라이브러리 구성

```bash
corpus
  ├── datasets.py
  ├── models.py
  └── utils
      ├── confluence_utils.py
      ├── elasticsearch_utils.py
      ├── logger.py
      ├── minio_utils.py
      └── webdav_utils.py
```

## datasets

```python
import pandas as pd
from corpus.datasets import DataSets

ds = DataSets()

# meta (minio) 정보 확인
meta = ds.get_meta('datasets')
print(meta)

# elasticsearch meta 정보 확인 
es_meta = ds.get_meta('elasticsearch')
print(es_meta)

data = ds.load(
    meta=meta,
    name='movie_reviews',
    filename='naver.reviews.json.bz2', 
)
print(f'count: {len(data):,}')

df = pd.DataFrame(data)
print(df)
```

## models

```python
from corpus.models import Models

m = Models()

# meta 정보 확인 
print(m.meta)

m.pull(name='bert', tag='002_bert_morp_tensorflow')
m.pull(name='bert', tag='004_bert_eojeol_tensorflow')
```

## jupyter notebook에서 package 경로 설정

```python
import sys

pkg_info = !pip3 show corpus
pkg_info = {l.split(':')[0]: l.split(': ')[1]  for l in pkg_info}

sys.path.append(pkg_info['Location'])

pkg_info, sys.path
```

# private pypi 로 설치

## /etc/hosts 에 nlp-utils 추가 

```bash
echo "172.19.153.41  nlp-utils" | sudo tee -a /etc/hosts

# nlp-utils.ncsoft.com
```

## ~/.pip/pip.conf 설정

```bash
cat <<EOF | tee ~/.pip/pip.conf                                                        
[global]
timeout = 120

index-url=https://k8s:nlplab@nlp-utils/repository/pypi/simple
trusted-host=nlp-utils
EOF
```

## 패키지 설치

```bash
pip3 install corpus
```

# 패키지 빌드/배포 

## wheel 빌드 

```bash
make clean build install
```

## 패키지 업로드 

```bash
make upload
```

## 패키지 확인

> https://nlp-utils/#browse/browse:pypi-hosted

## datasets cache

```bash
cache
  └── datasets
     ├── meta.json
     ├── movie_reviews
     │ ├── daum.json.bz2
     │ └── naver.json.bz2
     └── youtube
        └── replies
            ├── mtd.json.bz2
            └── news.json.bz2
```

## models cache

```bash
cache
  └── models
     ├── meta.json
     └── bert
        ├── 002_bert_morp_tensorflow.tar.bz2
        └── 002_bert_morp_tensorflow
           ├── bert_config.json
           ├── model.ckpt.data-00000-of-00001
           ├── model.ckpt.index
           ├── model.ckpt.meta
           ├── src_tokenizer
           │ └── tokenization_morp.py
           └── vocab.korean_morp.list
```

### datasets: meta.json

```json
{
  "movie_reviews": {
    "name": "movie_reviews",
    "desc": "네이버/다음 영화 리뷰",
    "format": "json",
    "location": "minio",
    "local_path": "movie_reviews",
    "remote_path": "movie_reviews",
    "tags": [
      "daum",
      "naver"
    ]
  },
  "youtube/replies": {
    "name": "youtube/replies",
    "desc": "유튜브 댓글",
    "format": "json",
    "location": "minio",
    "local_path": "youtube/replies",
    "remote_path": "youtube/replies",
    "tags": [
      "mtd",
      "news"
    ]
  }
}
```

### models: meta.json

```json
{
  "bert": {
    "name": "bert",
    "format": "tar.bz2",
    "desc": "버트 모델",
    "location": "minio",
    "local_path": "bert",
    "remote_path": "bert",
    "tags": [
      "002_bert_morp_tensorflow",
      "004_bert_eojeol_tensorflow"
    ]
  }
}
```

# 참고 

* [파이썬 package 배포 하기](https://rampart81.github.io/post/python_package_publish/)
* [Nexus3 를 이용하여 python private repository를 구축하자 - 3](http://blog.naver.com/dmzone75/221395643249)
* [[pypi] python private registry 구축하기 (pip)](https://waspro.tistory.com/559) 
