
# 베이스 코드
## https://github.com/ratsgo/embedding

# 도커 이미지 빌드 정보
GIT_TAG = $(shell git describe --tags --long | cut -f1,2 -d'-' | tr '-' '.')
GIT_URL = $(shell git config --get remote.origin.url)
GIT_BRANCH = $(shell git rev-parse --abbrev-ref HEAD)
GIT_COMMIT = $(shell git rev-list --count HEAD)
GIT_COMMIT_ID = $(shell git rev-parse --short HEAD)

BUILD_DATE = $(shell date +'%Y-%m-%d %H:%M:%S')

DOCKER_LABEL =
DOCKER_LABEL += --label "app=dev/embedding"
DOCKER_LABEL += --label "version=$(IMAGE_TAG)"
DOCKER_LABEL += --label "image_name=$(IMAGE_BASE)"
DOCKER_LABEL += --label "build-date=$(BUILD_DATE)"
DOCKER_LABEL += --label "git.url=$(GIT_URL)"
DOCKER_LABEL += --label "git.branch=$(GIT_BRANCH)"
DOCKER_LABEL += --label "git.tag=$(GIT_TAG)"
DOCKER_LABEL += --label "git.commit.id=$(GIT_COMMIT_ID)"
DOCKER_LABEL += --label "git.commit.count=$(GIT_COMMIT)"
DOCKER_LABEL += --build-arg "docker_tag=dev"
DOCKER_LABEL += --build-arg "docker_image=$(IMAGE_BASE)"
DOCKER_LABEL += --build-arg "build_date='$(BUILD_DATE)'"
DOCKER_LABEL += --build-arg "git_url=$(GIT_URL)"
DOCKER_LABEL += --build-arg "git_branch=$(GIT_BRANCH)"
DOCKER_LABEL += --build-arg "git_tag=$(GIT_TAG)"
DOCKER_LABEL += --build-arg "git_commit_id=$(GIT_COMMIT_ID)"
DOCKER_LABEL += --build-arg "git_commit_count=$(GIT_COMMIT)"

# 도커 이미지
IMAGE_PREFIX = registry.nlp-utils/dev

#BASE_IMAGE = tensorflow/tensorflow:2.3.0-gpu
BASE_IMAGE = tensorflow/tensorflow:2.3.0
#BASE_IMAGE = tensorflow/tensorflow:2.0.0-py3
#BASE_IMAGE = tensorflow/tensorflow:1.12.0-py3
#BASE_IMAGE = tensorflow/tensorflow:1.15.2-gpu-py3
#BASE_IMAGE = tensorflow/tensorflow:1.15.2-py3

IMAGE = $(IMAGE_PREFIX)/embedding
IMAGE_TAG = $(GIT_TAG).$(GIT_COMMIT)

# 도커 이미지명
IMAGE_BASE = $(IMAGE_PREFIX)/embedding:base
IMAGE_DEV = $(IMAGE):$(IMAGE_TAG)
IMAGE_KUBEFLOW = $(IMAGE_PREFIX)/utils/kubeflow-jupyter-lab:tf2.3-cpu

IMAGE_SPE = $(IMAGE_PREFIX)/utils/sentencepiece:latest
IMAGE_KONLPY = $(IMAGE_PREFIX)/utils/konlpy:latest
IMAGE_GLOVE = $(IMAGE_PREFIX)/utils/glove:latest
IMAGE_FASTTEXT = $(IMAGE_PREFIX)/utils/fast_text:latest
IMAGE_KHAIII = $(IMAGE_PREFIX)/utils/khaiii:latest
IMAGE_MECAB = $(IMAGE_PREFIX)/utils/mecab:latest
IMAGE_KOBERT = $(IMAGE_PREFIX)/utils/kobert:latest
IMAGE_KCBERT = $(IMAGE_PREFIX)/utils/kcbert:latest

BUILD_IMAGE =
BUILD_IMAGE += --build-arg "GLOVE=$(IMAGE_GLOVE)"
BUILD_IMAGE += --build-arg "MECAB=$(IMAGE_MECAB)"
BUILD_IMAGE += --build-arg "KHAIII=$(IMAGE_KHAIII)"
BUILD_IMAGE += --build-arg "FAST_TEXT=$(IMAGE_FASTTEXT)"
BUILD_IMAGE += --build-arg "SENTENCE_PIECE=$(IMAGE_SPE)"

# APT, PIP 미러
APT_CODE_NAME = bionic
APT_MIRROR = https://nlp-utils/repository/$(APT_CODE_NAME)
PIP_MIRROR = https://k8s:nlplab@nlp-utils/repository/pypi/simple
PIP_TRUST_HOST = nlp-utils

MIRROR =
MIRROR += --add-host "nlp-utils:172.19.153.41"
MIRROR += --build-arg "APT_MIRROR=$(APT_MIRROR)"
MIRROR += --build-arg "APT_CODE_NAME=$(APT_CODE_NAME)"
MIRROR += --build-arg "PIP_MIRROR=$(PIP_MIRROR)"
MIRROR += --build-arg "PIP_TRUST_HOST=$(PIP_TRUST_HOST)"

# 공통 도커 빌드 옵션
BUILD_OPT =
BUILD_OPT += --build-arg "UID=$(shell id -u)"
BUILD_OPT += --build-arg "GID=$(shell id -g)"
BUILD_OPT += --build-arg "MINIO_URI=http://172.19.168.48:9000"
BUILD_OPT += --build-arg "MINIO_BUCKET=minio"
BUILD_OPT += --build-arg "MINIO_TOKEN=minio123"

# PHONY
.PHONY: *

# type
batch: build push uninstall install
utils: sentencepiece konlpy glove fastText khaiii mecab

.ONESHELL:
sentencepiece:
	cd docker/sentencepiece/
	docker build $(MIRROR) $(BUILD_OPT) -t $(IMAGE_SPE) --build-arg "BASE_IMAGE=$(BASE_IMAGE)" .

.ONESHELL:
konlpy:
	cd docker/konlpy/
	docker build $(MIRROR) $(BUILD_OPT) -t $(IMAGE_KONLPY) --build-arg "BASE_IMAGE=$(BASE_IMAGE)" .

.ONESHELL:
glove:
	cd docker/glove/
	docker build $(MIRROR) $(BUILD_OPT) -t $(IMAGE_GLOVE) --build-arg "BASE_IMAGE=$(BASE_IMAGE)" .

.ONESHELL:
fastText:
	cd docker/fastText/
	docker build $(MIRROR) $(BUILD_OPT) -t $(IMAGE_FASTTEXT) --build-arg "BASE_IMAGE=$(BASE_IMAGE)" .

.ONESHELL:
khaiii:
	cd docker/khaiii/
	docker build $(MIRROR) $(BUILD_OPT) -t $(IMAGE_KHAIII) --build-arg "BASE_IMAGE=$(BASE_IMAGE)" .

.ONESHELL:
mecab:
	cd docker/mecab/
	docker build $(MIRROR) $(BUILD_OPT) -t $(IMAGE_MECAB) --build-arg "BASE_IMAGE=$(BASE_IMAGE)" .

.ONESHELL:
kobert:
	cd docker/kobert/
	docker build $(MIRROR) $(BUILD_OPT) -t $(IMAGE_KOBERT) --build-arg "BASE_IMAGE=$(BASE_IMAGE)" .

.ONESHELL:
kcbert:
	cd docker/kcbert/
	docker build $(MIRROR) $(BUILD_OPT) -t $(IMAGE_KCBERT) --build-arg "BASE_IMAGE=$(BASE_IMAGE)" .

.ONESHELL:
base:
	cd docker/base/
	docker build $(MIRROR) $(BUILD_OPT) $(DOCKER_LABEL) $(BUILD_IMAGE) -t $(IMAGE_BASE) \
		--build-arg "BASE_IMAGE=$(BASE_IMAGE)" .

.ONESHELL:
base-minio:
	cd docker/base_minio/
	docker build $(MIRROR) $(BUILD_OPT) $(DOCKER_LABEL) $(BUILD_IMAGE) -t $(IMAGE_BASE) \
		--build-arg "BASE_IMAGE=$(BASE_IMAGE)" .

.ONESHELL:
kubeflow:
	cd docker/kubeflow/
	docker build $(MIRROR) $(BUILD_OPT) $(DOCKER_LABEL) -t $(IMAGE_KUBEFLOW) \
		--build-arg "BASE_IMAGE=$(IMAGE_BASE)" .

.ONESHELL:
dev:
	cd docker/dev/
	docker build $(MIRROR) $(BUILD_OPT) $(DOCKER_LABEL) -t $(IMAGE_DEV)	\
		--build-arg "BASE_IMAGE=$(IMAGE_BASE)" .

	docker tag $(IMAGE):$(IMAGE_TAG) $(IMAGE):latest

.ONESHELL:
push:
	docker push $(IMAGE):$(IMAGE_TAG)
	docker push $(IMAGE):latest

.ONESHELL:
run:
	docker run \
		-it --rm \
		--hostname dev \
		--name embedding_dev \
		-u $(shell id -u):$(shell id -g) \
		--entrypoint /bin/bash \
		-v $(shell pwd):/home/user/embedding \
		$(IMAGE):latest

.ONESHELL:
jupyter:
	docker run \
		-it --rm \
		--hostname dev \
		-u $(shell id -u):$(shell id -g) \
		--name embedding_dev \
		-p 8888:8888 \
		-v $(shell pwd):/home/user/embedding \
		$(IMAGE):latest

.ONESHELL:
git-tag:
	git tag -a 1 -m 'version 1'

.ONESHELL:
upgrade_v2:
	tf_upgrade_v2 --intree models --outtree models_v2 --reportfile upgrade.log

# helm
.ONESHELL:
install:
	helm install node1 helm --set nodeName=node1 --set service.externalIPs=192.168.2.100

.ONESHELL:
uninstall:
	helm uninstall node1

.ONESHELL:
template:
	helm --debug template notebook
