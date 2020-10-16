
config:
	kubectl apply -f configmap.yaml

start-naver:
	helm install naver naver

test-naver:
	helm template naver --debug

start-daum:
	helm install daum daum

start-nate:
	helm install nate nate

stop-naver:
	helm uninstall naver

stop-daum:
	helm uninstall daum

stop-nate:
	helm uninstall nate

list:
	helm list

