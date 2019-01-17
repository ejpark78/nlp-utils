
VERSION = 2.0
DOCKER_REGISTRY = nlpapi:5000
CONTAINER = crawler

BASE_IMAGE = base/crawler:latest
IMAGE_NAME = $(DOCKER_REGISTRY)/crawler:$(VERSION)

default: build

.PHONY: base build push clean run

.ONESHELL:
base:
	rm app.tar.gz
	docker build -t $(BASE_IMAGE) -f Dockerfile.base .

.ONESHELL:
build:
	cd ../
	tar cvfz ./build/app.tar.gz \
		--exclude=.git \
		--exclude=.idea \
		--exclude=.vscode \
		--exclude=*.jar \
		--exclude=*.tar.gz \
		--exclude=*.pycharm* \
		--exclude=__pycache__ \
		--exclude=build \
		--exclude=data \
		--exclude=notebook \
		--exclude=wrap \
		--exclude=venv \
		--exclude=tmp \
		.

	cd build/
	docker build \
		-t $(IMAGE_NAME) \
		-f Dockerfile \
		.

push: 
	docker push $(IMAGE_NAME)

run: 
	docker run \
		-it --rm \
		--user crawler \
		--name $(CONTAINER) \
		-v /etc/hosts:/etc/hosts:ro \
		-v /etc/timezone:/etc/timezone:ro \
		-v /etc/localtime:/etc/localtime:ro \
		$(IMAGE_NAME)

test: 
	docker run \
		-it --rm \
		-v /etc/hosts:/etc/hosts:ro \
		-v $(PWD)/..:/usr/local/app \
		--name $(CONTAINER) \
		$(IMAGE_NAME)

major-press:
	docker-compose --project-directory crawler_major_press -f major-press.yml down
	docker-compose --project-directory crawler_major_press -f major-press.yml up -d
	docker-compose --project-directory crawler_major_press -f major-press.yml logs -f

naver-kin:
	docker-compose --project-directory crawler_naver_kin -f naver-kin.yml down
	docker-compose --project-directory crawler_naver_kin -f naver-kin.yml up -d
	docker-compose --project-directory crawler_naver_kin -f naver-kin.yml logs -f

naver:
	docker-compose --project-directory crawler-naver -f naver.yml down
	docker-compose --project-directory crawler-naver -f naver.yml up -d
	docker-compose --project-directory crawler-naver -f naver.yml logs -f

nate:
	docker-compose --project-directory crawler-nate -f nate.yml down
	docker-compose --project-directory crawler-nate -f nate.yml up -d
	docker-compose --project-directory crawler-nate -f nate.yml logs -f

daum:
	docker-compose --project-directory crawler-daum -f daum.yml down
	docker-compose --project-directory crawler-daum -f daum.yml up -d
	docker-compose --project-directory crawler-daum -f daum.yml logs -f

bbs:
	docker-compose --project-directory crawler-bbs -f bbs.yml down
	docker-compose --project-directory crawler-bbs -f bbs.yml up -d
	docker-compose --project-directory crawler-bbs -f bbs.yml logs -f

naver-logs:
	docker-compose --project-directory crawler-naver -f naver.yml logs -f

nate-logs:
	docker-compose --project-directory crawler-nate -f nate.yml logs -f

daum-logs:
	docker-compose --project-directory crawler-daum -f daum.yml logs -f

down-all:
	docker-compose --project-directory crawler-naver -f naver.yml down
	docker-compose --project-directory crawler-nate -f nate.yml down
	docker-compose --project-directory crawler-daum -f daum.yml down

twitter:
	docker-compose --project-directory crawler_twitter -f twitter.yml up -d

down:
	docker-compose --project-directory crawler_major_press -f major-press.yml down

batch-logs:
	docker-compose --project-directory crawler_major_press -f major-press.yml logs -f

bash:
	docker exec -it $(CONTAINER) /bin/bash

clean:
	docker system prune -f
