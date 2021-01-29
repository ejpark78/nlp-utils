
# 크롤러 쿠버네티스 helm 설정

# 실행

```bash
kubectl apply -f configmap.yaml

helm list

helm install naver . -f naver.yaml

helm upgrade naver . -f naver.yaml

helm uninstall naver
```

# configmap

```yaml
---
apiVersion: v1
kind: Secret
type: Opaque
metadata:
  name: elasticsearch-auth
data:
  http_auth: Y3Jhd2xlcjpjcmF3bGVyMjAxOQ==

---
apiVersion: v1
type: kubernetes.io/dockerconfigjson
kind: Secret
metadata:
  name: registry
data:
  .dockerconfigjson: eyJhdXRocyI6eyJyZWdpc3RyeS5ubHAtdXRpbHMiOnsidXNlcm5hbWUiOiJrOHMiLCJwYXNzd29yZCI6Im5scGxhYiIsImVtYWlsIjoiZWpwYXJrNzhAZ21haWwuY29tIiwiYXV0aCI6ImF6aHpPbTVzY0d4aFlnPT0ifX19

---
apiVersion: v1
kind: ConfigMap
metadata:
  name: naver
data:
  ELASTIC_SEARCH_HOST: "https://corpus.ncsoft.com:9200"
  INDEX_ECONOMY: "crawler-naver-economy"
  INDEX_INTERNATIONAL: "crawler-naver-international"
  INDEX_POLITICS: "crawler-naver-politics"
  INDEX_SOCIETY: "crawler-naver-society"
  INDEX_SPORTS: "crawler-naver-sports"
```

# cronjob helm

```yaml
image: registry.nlp-utils/crawler:live

imagePullSecrets: registry

restartPolicy: Never

resources:
  requests:
    cpu: 100m
    memory: 100Mi
  limits:
    cpu: 100m
    memory: 100Mi

hostAliases:
  - ip: "172.20.93.112"
    hostnames:
      - "corpus.ncsoft.com"

environmentVariables:
  - name: ELASTIC_SEARCH_AUTH
    valueFrom:
      secretKeyRef:
        name: elasticsearch-auth
        key: http_auth

schedule:
  concurrencyPolicy: Forbid
  failedJobsHistoryLimit: 1
  successfulJobsHistoryLimit: 1

jobs:
  - name: naver-economy
    schedule: "0 * * * *"
    configMapRef: naver
    environmentVariables:
      - name: ELASTIC_SEARCH_INDEX
        value: $(INDEX_ECONOMY)
    args:
      - "python3"
      - "-m"
      - "crawler.web_news.web_news"
      - "--config"
      - "/config/naver/economy.yaml"
      - "--sleep"
      - "20"
    subSategory:
      - "경제/증권"
      - "경제/금융"
      - "경제/부동산"
      - "경제/산업/재계"
      - "경제/글로벌 경제"
      - "경제/경제 일반"
      - "경제/생활경제"
      - "경제/중기/벤처"
```

# recrawler pod helm

```yaml
image: registry.nlp-utils/crawler:dev

imagePullSecrets: registry

restartPolicy: Never

resources:
  requests:
    cpu: 200m
    memory: 150Mi
  limits:
    cpu: 200m
    memory: 150Mi

hostAliases:
  - ip: "172.20.93.112"
    hostnames:
      - "corpus.ncsoft.com"

environmentVariables:
  - name: ELASTIC_SEARCH_AUTH
    valueFrom:
      secretKeyRef:
        name: elasticsearch-auth
        key: http_auth

jobs:
  - name: naver-economy
    environmentVariables:
      - name: ELASTIC_SEARCH_INDEX
        value: $(INDEX_ECONOMY)
    configMapRef: naver
    args:
      - "python3"
      - "-m"
      - "crawler.web_news.web_news"
      - "--config"
      - "/config/naver/economy.yaml"
      - "--date-range"
      - "2021-01-01~2021-01-28"
      - "--sleep"
      - "10"
    subSategory:
      - "경제/증권"
      - "경제/금융"
      - "경제/부동산"
      - "경제/산업/재계"
      - "경제/글로벌 경제"
      - "경제/경제 일반"
      - "경제/생활경제"
      - "경제/중기/벤처"

```

# 이미지 및 컨테이너 정리 

```bash
cat <<EOF > nodes
nc-crawler1
nc-crawler2
nc-crawler3
nc-crawler4
nc-crawler5
nc-crawler6
EOF

cls-p nodes "docker system prune -af"
```
