
.PHONY: *

SHELL := bash

.ONESHELL:
ls:
	helm ls -A

.ONESHELL:
upgrade:
	helm upgrade dev ./news -f news/dev.yaml -n dev
	helm upgrade ap-news ./news -f news/ap_news.yaml -n dev

	helm upgrade world-news ./news -f news/world.yaml -n dev
	helm upgrade korea-news ./news -f news/korea.yaml -n korea-news

	helm upgrade bbs ./portal -f portal/bbs.yaml -n bbs

	helm upgrade daum-news ./portal -f portal/daum-news.yaml -n dev
	helm upgrade nate-news ./portal -f portal/nate-news.yaml -n dev
	helm upgrade naver-news ./portal -f portal/naver-news.yaml -n dev

	helm upgrade naver-kin ./portal -f portal/naver-kin.yaml -n dev
	helm upgrade naver-reply ./portal -f portal/naver-reply.yaml -n dev

.ONESHELL:
install:
	helm install dev ./news -f news/dev.yaml -n dev
	helm install ap-news ./news -f news/ap_news.yaml -n dev

	helm install world-news ./news -f news/world.yaml -n dev
	helm install korea-news ./news -f news/korea.yaml -n korea-news

	helm install bbs ./portal -f portal/bbs.yaml -n bbs

	helm install daum-news ./portal -f portal/daum-news.yaml -n dev
	helm install nate-news ./portal -f portal/nate-news.yaml -n dev
	helm install naver-news ./portal -f portal/naver-news.yaml -n dev

	helm install naver-kin ./portal -f portal/naver-kin.yaml -n dev
	helm install naver-reply ./portal -f portal/naver-reply.yaml -n dev

.ONESHELL:
recrawler:
	helm install daum-news ./recrawler -f recrawler/daum-news.yaml -n recrawler-daum
	helm install nate-news ./recrawler -f recrawler/nate-news.yaml -n recrawler-nate
	helm install naver-news ./recrawler -f recrawler/naver-news.yaml -n recrawler-naver

.ONESHELL:
clean:
#	kubectl delete pods --field-selector status.phase!=Running -n naver-news
#	kubectl delete pods --field-selector status.phase!=Running -n recrawler-nate
#	kubectl delete pods --field-selector status.phase!=Running -n recrawler-daum

	cat <<EOS | xargs -I{} kubectl delete pods --field-selector status.phase!=Running -n {}
	dev
	korea-news
	world-news
	EOS

.ONESHELL:
logs:
	#stern '' -n dev
	stern '' -n recrawler-naver
