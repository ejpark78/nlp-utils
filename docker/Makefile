
.PHONY: *

# image
BASE_IMAGE = registry.nlp-utils/crawler

MAJOR_VERSION = $(shell git describe --tags --long | cut -f1 -d'-')
GIT_TAG = $(shell git describe --tags --long | cut -f1,2 -d'-' | tr '-' '.')
GIT_URL = $(shell git config --get remote.origin.url)
GIT_COMMIT = $(shell git rev-list --count HEAD)
GIT_COMMIT_ID = $(shell git rev-parse --short HEAD)
GIT_BRANCH = $(shell git rev-parse --abbrev-ref HEAD)

BUILD_DATE = $(shell date +'%Y-%m-%d %H:%M:%S')

IMAGE = registry.nlp-utils/crawler
IMAGE_TAG = $(GIT_TAG).$(GIT_COMMIT)

# Mirror
APT_CODE_NAME = focal
APT_MIRROR = https://nlp-utils/repository/$(APT_CODE_NAME)/
PIP_MIRROR = https://k8s:nlplab@nlp-utils/repository/pypi/simple
PIP_TRUST_HOST = nlp-utils

MIRROR =
MIRROR += --build-arg "APT_MIRROR=$(APT_MIRROR)"
MIRROR += --build-arg "APT_CODE_NAME=$(APT_CODE_NAME)"
MIRROR += --build-arg "PIP_MIRROR=$(PIP_MIRROR)"
MIRROR += --build-arg "PIP_TRUST_HOST=$(PIP_TRUST_HOST)"

# 도커 이미지 라벨
DOCKER_LABEL =
DOCKER_LABEL += --label "app=crawler"
DOCKER_LABEL += --label "version=$(IMAGE_TAG)"
DOCKER_LABEL += --label "image_name=$(IMAGE_BASE)"
DOCKER_LABEL += --label "build-date=$(BUILD_DATE)"
DOCKER_LABEL += --label "git.url=$(GIT_URL)"
DOCKER_LABEL += --label "git.branch=$(GIT_BRANCH)"
DOCKER_LABEL += --label "git.tag=$(GIT_TAG)"
DOCKER_LABEL += --label "git.commit.id=$(GIT_COMMIT_ID)"
DOCKER_LABEL += --label "git.commit.count=$(GIT_COMMIT)"

DOCKER_ARGS =
DOCKER_ARGS += --build-arg "DOCKER_TAG=$(IMAGE_TAG)"
DOCKER_ARGS += --build-arg "DOCKER_IMAGE=$(IMAGE)"
DOCKER_ARGS += --build-arg "BUILD_DATE='$(BUILD_DATE)'"
DOCKER_ARGS += --build-arg "GIT_URL=$(GIT_URL)"
DOCKER_ARGS += --build-arg "GIT_BRANCH=$(GIT_BRANCH)"
DOCKER_ARGS += --build-arg "GIT_TAG=$(GIT_TAG)"
DOCKER_ARGS += --build-arg "GIT_COMMIT_ID=$(GIT_COMMIT_ID)"
DOCKER_ARGS += --build-arg "GIT_COMMIT_COUNT=$(GIT_COMMIT)"

DOCKER_BUILD_OPT =
DOCKER_BUILD_OPT += --network=host
DOCKER_BUILD_OPT += --add-host "nlp-utils:172.19.153.41"
DOCKER_BUILD_OPT += --add-host "galadriel02.korea.ncsoft.corp:172.20.92.245"

batch: build push

.ONESHELL:
core:
	cd core

	docker build \
		$(MIRROR) \
		$(DOCKER_LABEL) \
		$(DOCKER_BUILD_OPT) \
		-t $(BASE_IMAGE):core \
		-f Dockerfile \
		.

.ONESHELL:
live:
	cd live

	docker build \
		$(DOCKER_LABEL) \
		$(DOCKER_ARGS) \
		$(DOCKER_BUILD_OPT) \
		--build-arg "INSTALL_BRANCH=live" \
		--build-arg "CONFIG_BRANCH=live" \
		-t $(IMAGE):live \
		-f Dockerfile \
		--build-arg BASE_IMAGE=$(BASE_IMAGE):core \
		.

.ONESHELL:
dev:
	cd live

	docker build \
		$(DOCKER_LABEL) \
		$(DOCKER_ARGS) \
		$(DOCKER_BUILD_OPT) \
		--build-arg "INSTALL_BRANCH=dev" \
		--build-arg "CONFIG_BRANCH=dev" \
		-t $(IMAGE):dev \
		-f Dockerfile \
		--build-arg BASE_IMAGE=$(BASE_IMAGE):core \
		.

.ONESHELL:
jupyter: live
	cd jupyter

	docker build \
		$(DOCKER_LABEL) \
		$(DOCKER_BUILD_OPT) \
		-t $(IMAGE):jupyter \
		-f Dockerfile \
		--build-arg BASE_IMAGE=$(BASE_IMAGE):core \
		.

.ONESHELL:
toolbox:
	cd toolbox

	docker build \
		$(MIRROR) \
		$(DOCKER_LABEL) \
		$(DOCKER_BUILD_OPT) \
		-t $(IMAGE):toolbox \
		-f Dockerfile \
		.

.ONESHELL:
push:
	docker push $(IMAGE):live
	docker push $(IMAGE):dev
	#docker push $(IMAGE):jupyter
	#docker push $(IMAGE):toolbox

.ONESHELL:
check-ip:
	@echo "Public IP: "
	@curl -s https://ipinfo.io/ip

	@echo "Local IP: "
	@hostname -I

.ONESHELL:
run:
	docker run \
		--rm \
		--name crawler \
		--network host \
		-e PORT=8888 \
		$(IMAGE):jupyter

.ONESHELL:
run-toolbox:
	docker run \
		-d \
		--name toolbox \
		--network host \
		--volume /var/run/docker.sock:/var/run/docker.sock \
		$(IMAGE):toolbox \
		ttyd -p 8081 --credential admin:searchT2020 zsh

.ONESHELL:
run-dev:
	docker run -it --rm \
		-e "ELASTIC_SEARCH_HOST=https://corpus.ncsoft.com:9200" \
		-e "ELASTIC_SEARCH_AUTH=crawler:crawler2019" \
		$(IMAGE):dev \
			python3 -m crawler.web_news.web_news \
				--sleep 10 \
				--config /config/naver-news.yaml \
				--job-name economy \
				--sub-category "경제/증권"

prune:
	cat nodes | xargs -I{} ssh {} "hostname ; docker system prune -af"
	cat nodes | xargs -I{} ssh {} "hostname ; docker images"

