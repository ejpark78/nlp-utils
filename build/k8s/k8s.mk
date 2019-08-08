
.ONESHELL:
k8s-naver-start:
	kubectl apply --namespace crawler -f k8s/naver.yaml

.ONESHELL:
k8s-nate-start:
	kubectl apply --namespace crawler -f k8s/nate.yaml

.ONESHELL:
k8s-daum-start:
	kubectl apply --namespace crawler -f k8s/daum.yaml
