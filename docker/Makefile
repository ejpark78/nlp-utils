
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
DOCKER_LABEL += --build-arg "docker_tag=$(IMAGE_TAG)"
DOCKER_LABEL += --build-arg "docker_image=$(IMAGE_BASE)"
DOCKER_LABEL += --build-arg "build_date='$(BUILD_DATE)'"
DOCKER_LABEL += --build-arg "git_url=$(GIT_URL)"
DOCKER_LABEL += --build-arg "git_branch=$(GIT_BRANCH)"
DOCKER_LABEL += --build-arg "git_tag=$(GIT_TAG)"
DOCKER_LABEL += --build-arg "git_commit_id=$(GIT_COMMIT_ID)"
DOCKER_LABEL += --build-arg "git_commit_count=$(GIT_COMMIT)"

DOCKER_BUILD_OPT =
DOCKER_BUILD_OPT += --network=host
DOCKER_BUILD_OPT += --add-host "nlp-utils:172.19.153.41"

batch: build push

.ONESHELL:
base:
	docker build \
		$(MIRROR) \
		$(DOCKER_BUILD_OPT) \
		-t $(BASE_IMAGE):base \
		-f base/Dockerfile \
		.

.ONESHELL:
build:
	cd ../src/
	tar cvfz ../docker/app.tar.gz \
		--exclude=__pycache__ \
		. ../requirements.txt

	cd -
	docker build \
		$(DOCKER_LABEL) \
		$(DOCKER_BUILD_OPT) \
		-t $(IMAGE):$(IMAGE_TAG) \
		-f Dockerfile \
		--build-arg BASE_IMAGE=$(BASE_IMAGE):base \
		.

	rm app.tar.gz

	docker tag $(IMAGE):$(IMAGE_TAG) $(IMAGE):$(MAJOR_VERSION)
	docker tag $(IMAGE):$(IMAGE_TAG) $(IMAGE):latest

.ONESHELL:
pull:
	docker pull $(IMAGE):$(IMAGE_TAG)
	docker pull $(IMAGE):latest

	source $(ENV_FILE)

	docker pull $$CRAWLER_IMAGE
	docker pull $$CORPUS_PROCESSOR_IMAGE

.ONESHELL:
push:
	docker push $(IMAGE):$(MAJOR_VERSION)
	docker push $(IMAGE):$(IMAGE_TAG)
	docker push $(IMAGE):latest

.ONESHELL:
check-ip:
	@echo "Public IP: "
	@curl -s https://ipinfo.io/ip

	@echo "Local IP: "
	@hostname -I

.ONESHELL:
run:
	docker run -d \
		--hostname crawler_dev \
		--name crawler_dev \
		-e PORT=8888 \
		-p 7777:8888 \
		-v $(shell realpath ../):/home/jovyan \
		$(BASE_IMAGE):base

prune:
	cat /etc/hosts \
		| grep nc-crawler \
		| perl -ple 's/\s+/\t/g' \
		| cut -f2 \
		| xargs -I{} ssh {} "docker system prune -f ; docker image prune -f -a"

# git-sync https://coffeewhale.com/kubernetes/git-sync/2020/02/22/git-sync/
