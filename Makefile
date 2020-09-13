
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
IMAGE_PREFIX = registry/dev

BASE_IMAGE = tensorflow/tensorflow:2.3.0-gpu
BASE_IMAGE = tensorflow/tensorflow:2.3.0
BASE_IMAGE = tensorflow/tensorflow:1.12.0-py3
BASE_IMAGE = tensorflow/tensorflow:1.15.2-gpu-py3
BASE_IMAGE = tensorflow/tensorflow:1.15.2-py3

IMAGE_BASE = $(IMAGE_PREFIX)/embedding:base

IMAGE = $(IMAGE_PREFIX)/embedding
IMAGE_TAG = $(GIT_TAG).$(GIT_COMMIT)

# APT, PIP 미러
#APT_CODE_NAME = bionic
#APT_MIRROR = https://nlp-utils/repository/$(APT_CODE_NAME)
#PIP_MIRROR = https://k8s:nlplab@nlp-utils/repository/pypi/simple
#PIP_TRUST_HOST = nlp-utils

MIRROR =
#MIRROR += --add-host "nlp-utils:172.19.153.41"
#MIRROR += --build-arg "APT_MIRROR=$(APT_MIRROR)"
#MIRROR += --build-arg "APT_CODE_NAME=$(APT_CODE_NAME)"
#MIRROR += --build-arg "PIP_MIRROR=$(PIP_MIRROR)"
#MIRROR += --build-arg "PIP_TRUST_HOST=$(PIP_TRUST_HOST)"

# 공통 도커 빌드 옵션
BUILD_OPT =
BUILD_OPT += --build-arg "UID=$(shell id -u)"
BUILD_OPT += --build-arg "GID=$(shell id -g)"
BUILD_OPT += --build-arg "BASE_IMAGE=$(BASE_IMAGE)"

# PHONY
.PHONY: *

# type
batch: build push uninstall install
utils: sentencepiece konlpy glove fastText khaiii mecab requirements

.ONESHELL:
sentencepiece:
	cd docker/sentencepiece/

	docker build \
		$(MIRROR) \
		$(BUILD_OPT) \
		-t $(IMAGE_PREFIX)/utils/sentencepiece:latest \
		-f Dockerfile \
		.

.ONESHELL:
konlpy:
	cd docker/konlpy/

	docker build \
		$(MIRROR) \
		$(BUILD_OPT) \
		-t $(IMAGE_PREFIX)/utils/konlpy:latest \
		-f Dockerfile \
		.

.ONESHELL:
glove:
	cd docker/glove/

	docker build \
		$(MIRROR) \
		$(BUILD_OPT) \
		-t $(IMAGE_PREFIX)/utils/glove:latest \
		-f Dockerfile \
		.

.ONESHELL:
fastText:
	cd docker/fastText/

	docker build \
		$(MIRROR) \
		$(BUILD_OPT) \
		-t $(IMAGE_PREFIX)/utils/fast_text:latest \
		-f Dockerfile \
		.

.ONESHELL:
khaiii:
	cd docker/khaiii/

	docker build \
		$(MIRROR) \
		$(BUILD_OPT) \
		-t $(IMAGE_PREFIX)/utils/khaiii:latest \
		-f Dockerfile \
		.

.ONESHELL:
mecab:
	cd docker/mecab/

	docker build \
		$(MIRROR) \
		$(BUILD_OPT) \
		-t $(IMAGE_PREFIX)/utils/mecab:latest \
		-f Dockerfile \
		.

.ONESHELL:
kobert:
	cd docker/kobert/

	docker build \
		$(MIRROR) \
		$(BUILD_OPT) \
		-t $(IMAGE_PREFIX)/utils/kobert:latest \
		-f Dockerfile \
		.

.ONESHELL:
kcbert:
	cd docker/kcbert/

	docker build \
		$(MIRROR) \
		$(BUILD_OPT) \
		-t $(IMAGE_PREFIX)/utils/kcbert:latest \
		-f Dockerfile \
		.

.ONESHELL:
requirements:
	cd docker/requirements/

	docker build \
		$(MIRROR) \
		$(BUILD_OPT) \
		-t $(IMAGE_PREFIX)/utils/requirements:latest \
		-f Dockerfile \
		.

.ONESHELL:
base:
	cd docker/base/

	docker build \
		$(MIRROR) \
		$(BUILD_OPT) \
		$(DOCKER_LABEL) \
		-t $(IMAGE_BASE) \
		--build-arg "GLOVE=$(IMAGE_PREFIX)/utils/glove:latest" \
		--build-arg "MECAB=$(IMAGE_PREFIX)/utils/mecab:latest" \
		--build-arg "KHAIII=$(IMAGE_PREFIX)/utils/khaiii:latest" \
		--build-arg "FAST_TEXT=$(IMAGE_PREFIX)/utils/fast_text:latest" \
		--build-arg "SENTENCE_PIECE=$(IMAGE_PREFIX)/utils/sentencepiece:latest" \
		-f Dockerfile \
		.

.ONESHELL:
dev:
	cd docker/dev/

	docker build \
		$(MIRROR) \
		$(BUILD_OPT) \
		$(DOCKER_LABEL) \
		-t $(IMAGE):$(IMAGE_TAG) \
		--build-arg "BASE_IMAGE=$(IMAGE_BASE)" \
		-f Dockerfile \
		.

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

#.ONESHELL:
#tuning:
#	PYTHONPATH=. python3 batch_tuner.py \
#		--model_name word \
#		--embedding_name random \
#		--model_save_path data/word-embeddings/random-tune \
#		--test_corpus_fname data/processed/processed_ratings_test.txt.bz2 \
#		--train_corpus_fname data/processed/processed_ratings_train.txt.bz2 \
#		| tee -a tune-random.log

#	bash preprocess.sh dump-processed
#	bash preprocess.sh dump-word-embeddings

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

#.ONESHELL:
#venv:
#	python3 -m venv venv
#	source venv/bin/activate
#	pip3 install -r requirements.txt
