
NAME=naver

.ONESHELL:
start-all:
	make NAME=international-news start

.ONESHELL:
stop-all:
	make NAME=international-news stop

.ONESHELL:
upgrade-all:
	make NAME=international-news upgrade

.ONESHELL:
config:
	kubectl apply -f configmap.yaml

.ONESHELL:
start:
	helm install $(NAME) . -f $(NAME).yaml

.ONESHELL:
upgrade:
	helm upgrade $(NAME) . -f $(NAME).yaml

.ONESHELL:
stop:
	helm uninstall $(NAME)

.ONESHELL:
test:
	helm template . -f $(NAME).yaml

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
