
.PHONY: *

SHELL := bash

.ONESHELL:
ls:
	helm ls -A

.ONESHELL:
install:
	#helm install pipeline ./pipeline -f pipeline/values.yaml -n pipeline-kb

	helm install bbs ./portal -f portal/bbs.yaml -n dev

	helm install daum-news ./portal -f portal/daum-news.yaml -n dev
	helm install nate-news ./portal -f portal/nate-news.yaml -n dev
	helm install naver-news ./portal -f portal/naver-news.yaml -n dev

	#helm install naver-kin ./portal -f portal/naver-kin.yaml -n naver-kin
	#helm install naver-reply ./portal -f portal/naver-reply.yaml -n dev

	helm list -A

#	helm install ap-news ./news -f news/ap_news.yaml -n dev
#
#	helm install world-news ./news -f news/world.yaml -n dev
#	helm install korea-news ./news -f news/korea.yaml -n dev

.ONESHELL:
upgrade:
#	helm upgrade ap-news ./news -f news/ap_news.yaml -n dev
#
#	helm upgrade world-news ./news -f news/world.yaml -n dev
#	helm upgrade korea-news ./news -f news/korea.yaml -n dev

	helm upgrade bbs ./portal -f portal/bbs.yaml -n dev

	helm upgrade daum-news ./portal -f portal/daum-news.yaml -n dev
	helm upgrade nate-news ./portal -f portal/nate-news.yaml -n dev
	helm upgrade naver-news ./portal -f portal/naver-news.yaml -n dev

#	helm upgrade naver-kin ./portal -f portal/naver-kin.yaml -n dev
#	helm upgrade naver-reply ./portal -f portal/naver-reply.yaml -n dev

	helm list -A

.ONESHELL:
delete:
#	helm delete ap-news -n dev
#	helm delete world-news -n dev
#	helm delete korea-news -n dev

	helm delete bbs -n dev
	helm delete daum-news -n dev
	helm delete nate-news -n dev
	helm delete naver-news -n dev
#	helm delete naver-kin -n dev
#	helm delete naver-reply -n dev

	#kubectl delete pods --field-selector status.phase!=Running -n dev

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
