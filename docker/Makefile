
.PHONY: *

# image
BASE_IMAGE = registry.nlp-utils/crawler-dev

MAJOR_VERSION = $(shell git describe --tags --long | cut -f1 -d'-')
GIT_TAG = $(shell git describe --tags --long | cut -f1,2 -d'-' | tr '-' '.')
GIT_URL = $(shell git config --get remote.origin.url)
GIT_COMMIT = $(shell git rev-list --count HEAD)
GIT_COMMIT_ID = $(shell git rev-parse --short HEAD)
GIT_BRANCH = $(shell git rev-parse --abbrev-ref HEAD)

BUILD_DATE = $(shell date +'%Y-%m-%d %H:%M:%S')

IMAGE = registry.nlp-utils/crawler-dev
IMAGE_TAG = $(GIT_TAG).$(GIT_COMMIT)

IMAGE_X11 = registry.nlp-utils/x11

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

# APP
APP_INSTALL =
APP_INSTALL += --build-arg "CRAWLER_SRC=http://ejpark:TNiMEsVDUcEnHEw6ozmM@galadriel02.korea.ncsoft.corp/crawler-dev/crawler.git"
APP_INSTALL += --build-arg "CRAWLER_CONFIG=http://ejpark:DswbvsDz31xEbRGwkqku@galadriel02.korea.ncsoft.corp/crawler-dev/config.git"

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
dev:
	cd dev

	docker build \
		$(MIRROR) \
		$(DOCKER_LABEL) \
		$(DOCKER_ARGS) \
		$(DOCKER_BUILD_OPT) \
		$(APP_INSTALL) \
		--build-arg "INSTALL_BRANCH=dev" \
		--build-arg "CONFIG_BRANCH=dev" \
		--build-arg BASE_IMAGE=$(BASE_IMAGE):core \
		-t $(IMAGE):dev \
		-f Dockerfile \
		.

.ONESHELL:
x11-core:
	cd x11/core

	docker build \
		$(MIRROR) \
		$(DOCKER_BUILD_OPT) \
		-t $(IMAGE_X11):core \
		-f Dockerfile \
		.

.ONESHELL:
xfce4:
	cd x11/xfce4

	docker build \
		$(MIRROR) \
		$(DOCKER_BUILD_OPT) \
		--build-arg BASE_IMAGE=$(IMAGE_X11):core \
		-t $(IMAGE_X11):xfce4 \
		-f Dockerfile \
		.

.ONESHELL:
xfce4-dev:
	cd x11/dev

	docker build \
		$(MIRROR) \
		$(DOCKER_BUILD_OPT) \
		--build-arg BASE_IMAGE=$(IMAGE_X11):xfce4 \
		-t $(IMAGE_X11):xfce4-dev \
		-f Dockerfile \
		.

.ONESHELL:
xfce4-selenium:
	cd xfce4/selenium

	docker build \
		$(MIRROR) \
		$(DOCKER_BUILD_OPT) \
		$(APP_INSTALL) \
		--build-arg BASE_IMAGE=$(IMAGE_X11):core \
		-t $(IMAGE_XFCE4):selenium \
		-f Dockerfile \
		.

.ONESHELL:
run-xfce4:
	docker run \
		-it --rm \
		--name xfce4 \
		--hostname xfce4 \
		--shm-size 1g \
		-p 5555:3389 \
		-p 5556:22 \
		$(IMAGE_X11):xfce4


.ONESHELL:
run-xfce4-dev:
	docker run \
		-d \
		--name xfce4-dev \
		--hostname xfce4-dev \
		--shm-size 1g \
		-p 5555:22 \
		--volume /home/ejpark/.kube:/home/ubuntu/.kube \
		--volume /home/ejpark/workspace:/home/ubuntu/ws \
		--volume /var/run/docker.sock:/var/run/docker.sock \
		$(IMAGE_X11):xfce4-dev

.ONESHELL:
stop-xfce4-dev:
	docker stop xfce4-dev
	docker rm xfce4-dev

.ONESHELL:
restart-xfce4-dev: stop-xfce4-dev run-xfce4-dev

.ONESHELL:
connect-xfce4:
	/opt/freerdp-nightly/bin/xfreerdp /cert:ignore /size:1600x1000 /u:ubuntu /v:localhost:5555

.ONESHELL:
connect-xfce4-dev:
	/opt/freerdp-nightly/bin/xfreerdp /cert:ignore /size:1600x1000 /u:ubuntu /v:localhost:5557

.ONESHELL:
jupyter: dev
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
push-dev:
	docker push $(IMAGE):dev

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
	docker run -d \
		--name toolbox \
		--network host \
		--volume /var/run/docker.sock:/var/run/docker.sock \
		$(IMAGE):toolbox \
		ttyd -p 8081 --credential admin:searchT2020 zsh

.ONESHELL:
reset-mirror-data:
	rm -rf $(shell pwd)/nexus3-data
	mkdir -p $(shell pwd)/nexus3-data/restore-from-backup

.ONESHELL:
mk-mirror-data:
	mkdir -p $(shell pwd)/nexus3-data/restore-from-backup
	tar xvfz $(shell pwd)/nexus3-config.tar.gz -C $(shell pwd)/nexus3-data/restore-from-backup

	sudo chown -R 200 $(shell pwd)/nexus3-data

	# nexus3 restore: https://help.sonatype.com/repomanager3/backup-and-restore/restore-exported-databases

.ONESHELL:
run-mirror:
	# id: nexus:nexus
	docker run -it --rm \
		--name nexus3 \
		-p 8081:8081 \
		--volume $(shell pwd)/nexus3-data:/nexus-data \
		sonatype/nexus3:latest

.ONESHELL:
run-upload-server:
	docker run -it --rm \
		-p 25478:25478 \
		--volume $(shell pwd)/tmp:/mnt \
		mayth/simple-upload-server -upload_limit 1024000000 -token token /mnt

	# curl 'http://172.19.153.41:25478/upload?token=token' -Ffile=@backup.tar.gz

	# https://github.com/mayth/go-simple-upload-server

