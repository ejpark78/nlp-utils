
# 크롤러 운영 방식

* k8s + cronjob
  - naver
    naver-kin
    naver-reply
    nate
    daum
    bbs
* k8s + airflow
  - korea_news
    world_news

# config

* crawler config
* airflow dag

# repo.

* source: http://galadriel02.korea.ncsoft.corp/crawler/crawler.git@master
  -> docker image
* config: http://galadriel02.korea.ncsoft.corp/crawler/config.git@live
  -> docker image
* operation k8s + cronjob (helm): http://galadriel02.korea.ncsoft.corp/searchtf/sapphire-server/nlp-cloud/crawler.git@master
  -> x
* operation k8s + airflow (dag): http://galadriel02.korea.ncsoft.corp/crawler/airflow.git@master
* airflow install: http://galadriel02.korea.ncsoft.corp/crawler/airflow-helm.git@master


# docker registry

* NC CLOUD: nlp-utils -> nexus3


# crawler config merge

```bash
# branch check
git branch -r

git checkout live

git pull origin youngjune

git commit -am 'merge youngjune'

git push origin live
```
