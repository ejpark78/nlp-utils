
config:
	kubectl apply -f configmap.yaml

start-naver:
	helm install naver naver

start-daum:
	helm install daum daum

start-nate:
	helm install nate nate

start-bbs:
	helm install bbs bbs

stop-naver:
	helm uninstall naver

stop-daum:
	helm uninstall daum

stop-nate:
	helm uninstall nate

stop-bbs:
	helm uninstall bbs

list:
	helm list

test:
	helm template naver --debug

