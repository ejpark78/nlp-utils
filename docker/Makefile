
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
base:
	docker build \
		$(MIRROR) \
		$(DOCKER_LABEL) \
		$(DOCKER_BUILD_OPT) \
		-t $(BASE_IMAGE):base \
		-f base/Dockerfile \
		.

.ONESHELL:
build:
	docker build \
		$(DOCKER_LABEL) \
		$(DOCKER_ARGS) \
		$(DOCKER_BUILD_OPT) \
		-t $(IMAGE):$(IMAGE_TAG) \
		-f live/Dockerfile \
		--build-arg BASE_IMAGE=$(BASE_IMAGE):base \
		.

.ONESHELL:
dev:
	cd ../
	tar cvfz ./docker/app.tar.gz \
		--exclude=.git* \
		--exclude=.idea \
		--exclude=log \
		--exclude=ops \
		--exclude=venv \
		--exclude=data \
		--exclude=dist \
		--exclude=cache \
		--exclude=build \
		--exclude=notebook \
		--exclude=__pycache__ \
		.

	cd -
	docker build \
		$(DOCKER_LABEL) \
		$(DOCKER_ARGS) \
		$(DOCKER_BUILD_OPT) \
		-t $(IMAGE):dev \
		-f dev/Dockerfile \
		--build-arg BASE_IMAGE=$(BASE_IMAGE):base \
		.

	rm app.tar.gz

.ONESHELL:
jupyter: dev
	docker build \
		$(DOCKER_LABEL) \
		$(DOCKER_BUILD_OPT) \
		-t $(IMAGE):jupyter \
		-f jupyter/Dockerfile \
		--build-arg BASE_IMAGE=$(BASE_IMAGE):dev \
		.

.ONESHELL:
k9s:
	docker build \
		$(DOCKER_LABEL) \
		$(DOCKER_BUILD_OPT) \
		-t $(IMAGE):k9s \
		-f k9s/Dockerfile \
		.

.ONESHELL:
live: build
	docker tag $(IMAGE):$(IMAGE_TAG) $(IMAGE):live

.ONESHELL:
push:
	docker push $(IMAGE):dev
	docker push $(IMAGE):live
	docker push $(IMAGE):jupyter
	docker push $(IMAGE):$(IMAGE_TAG)

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

prune:
	cat nodes | xargs -I{} ssh {} "hostname ; docker system prune -af"
	cat nodes | xargs -I{} ssh {} "hostname ; docker images"

