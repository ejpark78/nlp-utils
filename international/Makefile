
NAME=naver

.ONESHELL:
start-all:
	make NAME=news start

.ONESHELL:
stop-all:
	make NAME=news stop

.ONESHELL:
upgrade-all:
	make NAME=news upgrade

.ONESHELL:
config:
	kubectl apply -f configmap.yaml

.ONESHELL:
start:
	helm install $(NAME) . -f values.yaml

.ONESHELL:
upgrade:
	helm upgrade $(NAME) . -f values.yaml

.ONESHELL:
stop:
	helm uninstall $(NAME)

.ONESHELL:
test:
	helm template . -f values.yaml

.ONESHELL:
list:
	helm list

.ONESHELL:
prune:
	cat /etc/hosts \
		| grep nc-crawler \
		| perl -ple 's/\s+/\t/g' \
		| cut -f2 \
		| xargs -I{} ssh {} "docker system prune -f ; docker image prune -f -a"
