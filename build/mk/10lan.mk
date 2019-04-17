
ELASTIC_NETWORK_HOST = _ens3_

LOGSTASH_IMAGE = corpus:5000/elk/logstash:6.7.1
FILEBEAT_IMAGE = corpus:5000/elk/filebeat:6.7.1

KIBANA_IMAGE = corpus:5000/elk/kibana:6.7.1
ELASTIC_IMAGE = corpus:5000/elk/elasticsearch:6.7.1

PORTAINER_IMAGE = portainer/portainer:latest
RABBIT_MQ_IMAGE = rabbitmq:3-management

.ONESHELL:
10lan-ssh-tunnel:
	ssh -L 5601:localhost:5601 -L 9000:localhost:9000 nlpdev@10.242.94.49

.ONESHELL:
10lan-elastic:
	docker stop elasticsearch
	docker rm elasticsearch

	docker run \
		-d --restart=unless-stopped \
		--privileged \
		--network host \
		--ulimit memlock=-1:-1 \
		--user elstack \
		--name elasticsearch \
		--log-driver json-file \
		--log-opt max-size=100m \
		--log-opt max-file=3 \
		-e "RUN_MODE=master" \
		-e "NODE_NAME=$(shell hostname)" \
		-e "ES_JAVA_OPTS=-Xms8g -Xmx8g" \
		-e "UNICAST_HOSTS=paige-elk-01,paige-elk-02,paige-elk-03" \
		-e "NETWORK_HOST=${ELASTIC_NETWORK_HOST}" \
		-e "bootstrap.memory_lock=true" \
		-v "/etc/timezone:/etc/timezone:ro" \
		-v "/etc/localtime:/etc/localtime:ro" \
		-v "/home/docker/elastic/data:/usr/share/elasticsearch/data:rw" \
		-v "/home/docker/elastic/snapshot:/snapshot:rw" \
		$(ELASTIC_IMAGE)

.ONESHELL:
10lan-kibana:
	docker stop kibana
	docker rm kibana

	docker run \
		-d --restart=unless-stopped \
		--name kibana \
		--log-driver json-file \
		--log-opt max-size=100m \
		--log-opt max-file=3 \
		-p 5601:5601 \
		-e "ELASTICSEARCH_HOSTS=http://paige-elk-01:9200" \
		-e "ES_JAVA_OPTS=-Xms2g -Xmx2g" \
		-v "/etc/timezone:/etc/timezone:ro" \
		-v "/etc/localtime:/etc/localtime:ro" \
		--add-host "paige-elk-01:10.242.94.49" \
		--add-host "paige-elk-02:10.242.94.50" \
		--add-host "paige-elk-03:10.242.94.51" \
		$(KIBANA_IMAGE)

.ONESHELL:
10lan-filebeat:
	docker stop filebeat_corpus_processor
	docker rm filebeat_corpus_processor

	docker run \
		-d --restart=unless-stopped \
		--privileged \
		--name filebeat_corpus_processor \
		--hostname $(shell hostname) \
		--network host \
		--log-driver json-file \
		--log-opt max-size=100m \
		--log-opt max-file=3 \
		-e "CONF=conf.d/corpus_processor.yml" \
		-v "/etc/timezone:/etc/timezone:ro" \
		-v "/etc/localtime:/etc/localtime:ro" \
		-v "/var/run/docker.sock:/var/run/docker.sock:ro" \
		-v "/var/lib/docker/containers:/var/lib/docker/containers:ro" \
		--add-host "logstash:10.242.94.49" \
		--add-host "kibana:10.242.94.49" \
		--add-host "elasticsearch:10.242.94.49" \
		$(FILEBEAT_IMAGE)

	docker stop filebeat_crawler
	docker rm filebeat_crawler

	docker run \
		-d --restart=unless-stopped \
		--privileged \
		--name filebeat_crawler \
		--hostname $(shell hostname) \
		--network host \
		--log-driver json-file \
		--log-opt max-size=100m \
		--log-opt max-file=3 \
		-e "CONF=conf.d/crawler.yml" \
		-v "/etc/timezone:/etc/timezone:ro" \
		-v "/etc/localtime:/etc/localtime:ro" \
		-v "/var/run/docker.sock:/var/run/docker.sock:ro" \
		-v "/var/lib/docker/containers:/var/lib/docker/containers:ro" \
		--add-host "logstash:10.242.94.49" \
		--add-host "kibana:10.242.94.49" \
		--add-host "elasticsearch:10.242.94.49" \
		$(FILEBEAT_IMAGE)

.ONESHELL:
10lan-logstash:
	docker stop logstash_crawler
	docker rm logstash_crawler

	docker run \
		-d --restart=unless-stopped \
		--privileged \
		--name logstash_crawler \
		--hostname logstash_crawler \
		--network host \
		--log-driver json-file \
		--log-opt max-size=100m \
		--log-opt max-file=3 \
		-e "CONF=config/crawler.conf" \
		-v "/etc/timezone:/etc/timezone:ro" \
		-v "/etc/localtime:/etc/localtime:ro" \
		--add-host "elasticsearch:10.242.94.49" \
		$(LOGSTASH_IMAGE)

.ONESHELL:
10lan-portainer:
	docker stop portainer
	docker rm portainer

	docker run \
		-d --restart=unless-stopped \
		-p 9000:9000 \
		-v /home/docker/portainer:/data \
		-v /var/run/docker.sock:/var/run/docker.sock \
		--name portainer \
		--add-host "paige-elk-01:10.242.94.49" \
		--add-host "paige-elk-02:10.242.94.50" \
		--add-host "paige-elk-03:10.242.94.51" \
		$(PORTAINER_IMAGE)

.ONESHELL:
10lan-env:
	echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
	sudo sysctl -p --system

	sudo chown -R 1000:1000 /home/docker/elastic

.ONESHELL:
10lan-sync:
	rsync -avz ~/build/ paige-elk-02:build/
	rsync -avz ~/build/ paige-elk-03:build/

	rsync -avz ~/docker-images/ paige-elk-02:docker-images/
	rsync -avz ~/docker-images/ paige-elk-03:docker-images/

	rsync -avz ./ paige-elk-02:$(shell pwd)/
	rsync -avz ./ paige-elk-03:$(shell pwd)/

.ONESHELL:
10lan-save:
	source $(ENV_FILE)

	docker save $$CRAWLER_IMAGE | gzip > crawler.tar.gz
	docker save $$CORPUS_PROCESSOR_IMAGE | gzip > corpus-processor.tar.gz

#	docker save $(LOGSTASH_IMAGE) | gzip > logstash.tar.gz
#	docker save $(FILEBEAT_IMAGE) | gzip > filebeat.tar.gz
#
#	docker save $(KIBANA_IMAGE) | gzip > kibana.tar.gz
#	docker save $(ELASTIC_IMAGE) | gzip > elastic.tar.gz
#
#	docker save $(PORTAINER_IMAGE) | gzip > portainer.tar.gz
#	docker save $(RABBIT_MQ_IMAGE) | gzip > rabbitmq.tar.gz

.ONESHELL:
10lan-load:
	docker load < crawler.tar.gz
	docker load < corpus-processor.tar.gz

#	docker load < logstash.tar.gz
#	docker load < filebeat.tar.gz

#	docker load < rabbitmq.tar.gz
#	docker load < portainer.tar.gz
#
#	docker load < kibana.tar.gz
#	docker load < elastic.tar.gz

#	docker load < portainer.tar.gz
#	docker load < rabbitmq.tar.gz

.ONESHELL:
10lan-setup-file:
	tar cvf paige-setup-$(shell date -I).tar *.env *.tar.gz Makefile mk

## 메모
# /etc/hosts 파일에서 paige-elk-01 의 아이피 127.0.1.1 을 주석처리한다.
#127.0.1.1 paige-elk-01
#127.0.0.1 localhost

#10.242.94.49 paige-elk-01
#10.242.94.50 paige-elk-02
#10.242.94.51 paige-elk-03

# docker 데몬 옵션
# /usr/bin/dockerd
#   -H fd:// -H tcp://0.0.0.0:2376 -H unix:///var/run/docker.sock
#   --tlsverify --tlscacert=/etc/docker/ca.pem --tlscert=/etc/docker/server-cert.pem --tlskey=/etc/docker/server-key.pem
#   --dns=8.8.8.8 --dns=172.20.0.87 --dns=172.20.0.88
#   --bip=192.168.0.1/16
#   --insecure-registry=corpus:5000

# make CRAWLER_OPT="-re_crawl -date_range 2000-01-01~2018-12-10" paige-recrawl

#$ cat ~/.docker/config.json
#{
#	"psFormat": "table {{.Names}}\t{{.Image}}\t{{.Status}}",
#	"statsFormat": "table {{.Name}}\t{{.CPUPerc}} / {{.MemUsage}} / {{.MemPerc}}\t{{.NetIO}} / {{.BlockIO}}"
#}

