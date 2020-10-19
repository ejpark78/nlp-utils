
NAME=naver

config:
	kubectl apply -f configmap.yaml

start:
	helm install $(NAME) . -f $(NAME).yaml

stop:
	helm uninstall $(NAME) . -f $(NAME).yaml

test:
	helm template . -f $(NAME).yaml

list:
	helm list

