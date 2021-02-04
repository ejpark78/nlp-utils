
# fluentd DaemonSet 설치 방법

* https://github.com/fluent/fluentd-kubernetes-daemonset
* https://medium.com/kubernetes-tutorials/cluster-level-logging-in-kubernetes-with-fluentd-e59aa2b6093a
* https://github.com/fluent/fluentd/issues/2073

```bash
wget https://raw.githubusercontent.com/fluent/fluentd-kubernetes-daemonset/master/fluentd-daemonset-elasticsearch-rbac.yaml
```

## NC CLOUD Security Group 설정

* nlp-crawler outbound 설정

> port: 9200
> IP: 172.19.169.47

* rook-elk inbound 설정

> port: 9200 
> Group: NCC Work_Dev 4 (172.19.168.0/22)

## ConfigMap

```yaml
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-config
data:
  crawler.conf: |
    <filter kubernetes.var.log.containers.**>
      @type parser
      <parse>
        @type json
        json_parser json
      </parse>
      replace_invalid_sequence true
      emit_invalid_record_to_error false
      key_name log
      reserve_data true
    </filter>

```

## Docker Registry Secret

```yaml
---
apiVersion: v1
type: kubernetes.io/dockerconfigjson
kind: Secret
metadata:
  name: fluentd-registry
  namespace: kube-system
data:
  .dockerconfigjson: eyJhdXRocyI6eyJyZWdpc3RyeS5ubHAtdXRpbHMiOnsidXNlcm5hbWUiOiJrOHMiLCJwYXNzd29yZCI6Im5scGxhYiIsImVtYWlsIjoiZWpwYXJrNzhAZ21haWwuY29tIiwiYXV0aCI6ImF6aHpPbTVzY0d4aFlnPT0ifX19

```

## DaemonSet config 

```yaml
---
apiVersion: apps/v1
kind: DaemonSet
spec:
  template:
    spec:
      containers:
      - name: fluentd
        image: registry.nlp-utils/fluent/fluentd-kubernetes-daemonset:v1-debian-elasticsearch
        env:
          - name:  FLUENT_ELASTICSEARCH_HOST
            value: "172.19.169.47"
          - name:  FLUENT_ELASTICSEARCH_PORT
            value: "9200"
          - name: FLUENT_ELASTICSEARCH_SCHEME
            value: "https"
          - name: FLUENT_ELASTICSEARCH_SSL_VERIFY
            value: "false"
          - name: FLUENT_ELASTICSEARCH_SSL_VERSION
            value: "TLSv1_2"
          - name: FLUENT_ELASTICSEARCH_USER
            value: "elastic"
          - name: FLUENT_ELASTICSEARCH_PASSWORD
            value: "searchT2020"
        volumeMounts:
        - name: fluentd-config
          mountPath: /fluentd/etc/conf.d
      volumes:
      - name: fluentd-config
        configMap:
          name: fluentd-config
```
