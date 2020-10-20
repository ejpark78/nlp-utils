
NAME=naver

config:
	kubectl apply -f configmap.yaml

start-all:
	make NAME=naver start
	make NAME=daum start
	make NAME=nate start
	make NAME=naver-terms start

stop-all:
	make NAME=naver stop
	make NAME=daum stop
	make NAME=nate stop
	make NAME=naver-terms stop

start:
	helm install $(NAME) . -f $(NAME).yaml

stop:
	helm uninstall $(NAME)

test:
	helm template . -f $(NAME).yaml

list:
	helm list

prune:
	cat /etc/hosts \
		| grep nc-crawler \
		| perl -ple 's/\s+/\t/g' \
		| cut -f2 \
		| xargs -I{} ssh {} "docker system prune -f ; docker image prune -f -a"
