
NAME=naver

.ONESHELL:
start-all:
	make NAME=bbs start
	make NAME=nate start
	make NAME=daum start
	make NAME=naver start
	make NAME=naver-kin start
	make NAME=naver-reply start

.ONESHELL:
stop-all:
	make NAME=bbs stop
	make NAME=nate stop
	make NAME=daum stop
	make NAME=naver stop
	make NAME=naver-kin stop
	make NAME=naver-reply stop

.ONESHELL:
upgrade-all:
	make NAME=bbs upgrade
	make NAME=nate upgrade
	make NAME=daum upgrade
	make NAME=naver upgrade
	make NAME=naver-kin upgrade
	make NAME=naver-reply upgrade

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
