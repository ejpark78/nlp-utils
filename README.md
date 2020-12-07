
# 사용법 

## 설치 

```bash
pip3 install git+http://galadriel02.korea.ncsoft.corp/searchtf/pypi/nlplab.git
```

## datasets

```python
import pandas as pd
from nlplab.datasets import DataSets

ds = DataSets()

# meta (minio) 정보 확인 
print(ds.meta)

# elasticsearch meta 정보 확인 
ds.pull_elastic_meta()
print(ds.meta)

ds.pull_minio_file(name='movie_reviews', tag='daum')
ds.pull_minio_file(name='movie_reviews', tag='naver')

data = ds.load(name='movie_reviews')

df = pd.DataFrame(data['daum'])
print(df)
```

## models

```python
from nlplab.models import Models

m = Models()

# meta 정보 확인 
print(m.meta)

m.pull(name='bert', tag='002_bert_morp_tensorflow')
m.pull(name='bert', tag='004_bert_eojeol_tensorflow')
```

## jupyter notebook에서 package 경로 설정

```python
import sys

pkg_info = !pip3 show nlplab
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
pip3 install nlplab
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

# 참고 

* [파이썬 package 배포 하기](https://rampart81.github.io/post/python_package_publish/)
* [Nexus3 를 이용하여 python private repository를 구축하자 - 3](http://blog.naver.com/dmzone75/221395643249)
* [[pypi] python private registry 구축하기 (pip)](https://waspro.tistory.com/559) 
