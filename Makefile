
# 베이스 코드
## https://github.com/ratsgo/embedding

# 도커 이미지 빌드 정보
GIT_TAG = $(shell git describe --tags --long | cut -f1,2 -d'-' | tr '-' '.')
GIT_URL = $(shell git config --get remote.origin.url)
GIT_BRANCH = $(shell git rev-parse --abbrev-ref HEAD)
GIT_COMMIT = $(shell git rev-list --count HEAD)
GIT_COMMIT_ID = $(shell git rev-parse --short HEAD)

BUILD_DATE = $(shell date +'%Y-%m-%d %H:%M:%S')

# 도커 이미지
DOCKER_REGISTRY = registry.nlp-utils

BASE_IMAGE = tensorflow/tensorflow:2.3.0-gpu
#BASE_IMAGE = tensorflow/tensorflow:2.3.0

#BASE_IMAGE = tensorflow/tensorflow:2.0.0-py3
#BASE_IMAGE = tensorflow/tensorflow:1.12.0-py3
#BASE_IMAGE = tensorflow/tensorflow:1.15.2-gpu-py3
#BASE_IMAGE = tensorflow/tensorflow:1.15.2-py3

IMAGE = $(DOCKER_REGISTRY)/utils
IMAGE_TAG = tf2.3.0-cpu
#IMAGE_TAG = tf2.3.0-gpu

# 도커 이미지명
IMAGE_DEV = $(DOCKER_REGISTRY)/utils/dev:$(IMAGE_TAG)
IMAGE_BASE = $(DOCKER_REGISTRY)/utils/base:$(IMAGE_TAG)
IMAGE_MLFLOW = $(DOCKER_REGISTRY)/utils/mlflow:$(IMAGE_TAG)

IMAGE_JUPYTER = $(DOCKER_REGISTRY)/utils/jupyter:$(IMAGE_TAG)
IMAGE_KUBEFLOW_JUPYTER = kubeflow-registry.default.svc.cluster.local:30000/jupyter:$(IMAGE_TAG)

IMAGE_SPE = $(DOCKER_REGISTRY)/utils/sentencepiece:$(IMAGE_TAG)
IMAGE_MECAB = $(DOCKER_REGISTRY)/utils/mecab:$(IMAGE_TAG)
IMAGE_GLOVE = $(DOCKER_REGISTRY)/utils/glove:$(IMAGE_TAG)
IMAGE_KONLPY = $(DOCKER_REGISTRY)/utils/konlpy:$(IMAGE_TAG)
IMAGE_KHAIII = $(DOCKER_REGISTRY)/utils/khaiii:$(IMAGE_TAG)
IMAGE_KOBERT = $(DOCKER_REGISTRY)/utils/kobert:$(IMAGE_TAG)
IMAGE_KCBERT = $(DOCKER_REGISTRY)/utils/kcbert:$(IMAGE_TAG)
IMAGE_FASTTEXT = $(DOCKER_REGISTRY)/utils/fast_text:$(IMAGE_TAG)

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
MINIO_URI = "http://$(shell hostname -I | cut -f1 -d' '):9000"
MINIO_ACCESS_KEY = "minio"
MINIO_SECRET_KEY = "minio123"
MINIO_BUCKET = "cache"
MINIO_PATH = $(IMAGE_TAG)

MINIO =
MINIO += --build-arg "MINIO_URI=$(MINIO_URI)"
MINIO += --build-arg "MINIO_ACCESS_KEY=$(MINIO_ACCESS_KEY)"
MINIO += --build-arg "MINIO_SECRET_KEY=$(MINIO_SECRET_KEY)"
MINIO += --build-arg "MINIO_BUCKET=$(MINIO_BUCKET)"
MINIO += --build-arg "MINIO_PATH=$(MINIO_PATH)"

# 도커 이미지 라벨
DOCKER_LABEL =
DOCKER_LABEL += --label "app=dev/nlp-utils"
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

# PHONY
.PHONY: *

# type
all: start-minio utils batch stop-minio
batch: start-minio base mlflow jupyter dev stop-minio
utils: sentencepiece konlpy glove fastText khaiii mecab

.ONESHELL:
start-minio:
	docker run \
		-d \
		--name minio \
		-p 9000:9000 \
		-v $(shell pwd)/.cache:/data:rw \
		-e "MINIO_ACCESS_KEY=$(MINIO_ACCESS_KEY)" \
		-e "MINIO_SECRET_KEY=$(MINIO_SECRET_KEY)" \
		minio/minio server /data

	mc alias set $(MINIO_BUCKET) ${MINIO_URI} ${MINIO_ACCESS_KEY} ${MINIO_SECRET_KEY}
	mc mb $(MINIO_BUCKET)/$(MINIO_PATH)

.ONESHELL:
stop-minio:
	docker stop minio
	docker rm minio

.ONESHELL:
clean-minio:
	sudo rm -rf $(shell pwd)/.cache

.ONESHELL:
sentencepiece:
	cd docker/sentencepiece/
	docker build $(MIRROR) $(MINIO) \
		--build-arg "BASE_IMAGE=$(BASE_IMAGE)" \
		-t $(IMAGE_SPE) \
		.

.ONESHELL:
konlpy:
	cd docker/konlpy/
	docker build $(MIRROR) $(MINIO) \
		--build-arg "BASE_IMAGE=$(BASE_IMAGE)" \
		-t $(IMAGE_KONLPY) \
		.

.ONESHELL:
glove:
	cd docker/glove/
	docker build $(MIRROR) $(MINIO) \
		--build-arg "BASE_IMAGE=$(BASE_IMAGE)" \
		-t $(IMAGE_GLOVE) \
		.

.ONESHELL:
fastText:
	cd docker/fastText/
	docker build $(MIRROR) $(MINIO) \
		--build-arg "BASE_IMAGE=$(BASE_IMAGE)" \
		-t $(IMAGE_FASTTEXT) \
		.

.ONESHELL:
khaiii:
	cd docker/khaiii/
	docker build $(MIRROR) $(MINIO) \
		--build-arg "BASE_IMAGE=$(BASE_IMAGE)" \
		-t $(IMAGE_KHAIII) \
		.

.ONESHELL:
mecab:
	cd docker/mecab/
	docker build $(MIRROR) $(MINIO) \
		--build-arg "BASE_IMAGE=$(BASE_IMAGE)" \
		-t $(IMAGE_MECAB) \
		.

.ONESHELL:
base:
	cd docker/base/
	docker build $(MIRROR) $(MINIO) $(DOCKER_LABEL) \
		--build-arg "BASE_IMAGE=$(BASE_IMAGE)" \
		-t $(IMAGE_BASE) \
		.

.ONESHELL:
base-stage:
	cd docker/base-stage/
	docker build $(MIRROR) $(MINIO) $(DOCKER_LABEL) $(BUILD_IMAGE) \
		--build-arg "BASE_IMAGE=$(BASE_IMAGE)" \
		-t $(IMAGE_BASE) \
		.

.ONESHELL:
kubeflow:
	cd docker/kubeflow/
	docker build $(MIRROR) $(DOCKER_LABEL) \
		--build-arg "BASE_IMAGE=$(IMAGE_BASE)" \
		-t $(IMAGE_JUPYTER) \
		.

	docker tag $(IMAGE_JUPYTER) $(IMAGE_KUBEFLOW_JUPYTER)

.ONESHELL:
mlflow:
	cd docker/mlflow/
	docker build $(MIRROR) $(DOCKER_LABEL) \
		--build-arg "BASE_IMAGE=$(IMAGE_BASE)" \
		-t $(IMAGE_MLFLOW) \
		.

.ONESHELL:
dev:
	cd docker/dev/
	docker build $(MIRROR) $(MINIO) $(DOCKER_LABEL) \
		--build-arg "BASE_IMAGE=$(IMAGE_BASE)" \
		-t $(IMAGE_DEV)	\
		.

.ONESHELL:
push:
	docker push $(IMAGE_DEV)
	docker push $(IMAGE_JUPYTER)
	docker push $(IMAGE_KUBEFLOW_JUPYTER)

.ONESHELL:
run-dev:
	docker run \
		-it --rm \
		--hostname dev \
		--name embedding_dev \
		--entrypoint /bin/bash \
		-p 8888:8888 \
		-v $(shell pwd):/home/user/embedding \
		$(IMAGE_DEV)

.ONESHELL:
git-tag:
	git tag -a 1 -m 'version 1'
