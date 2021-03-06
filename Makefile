
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
#DOCKER_REGISTRY = registry.nlp-utils
#DOCKER_REGISTRY = kubeflow-registry.default.svc.cluster.local:30000
DOCKER_REGISTRY = registry

IMAGE_TAG = 2.3.0
#IMAGE_TAG = 2.3.0-gpu
#IMAGE_TAG = 1.15.2-gpu-py3
#IMAGE_TAG = 1.15.2-py3

BASE_IMAGE = tensorflow/tensorflow:$(IMAGE_TAG)

IMAGE = $(DOCKER_REGISTRY)/utils

# 도커 이미지명
IMAGE_DEV = $(DOCKER_REGISTRY)/utils/dev:$(IMAGE_TAG)
IMAGE_BASE = $(DOCKER_REGISTRY)/utils/base:$(IMAGE_TAG)
IMAGE_MLFLOW = $(DOCKER_REGISTRY)/utils/mlflow:$(IMAGE_TAG)

IMAGE_KUBEFLOW = $(DOCKER_REGISTRY)/utils/kubeflow:$(IMAGE_TAG)
IMAGE_KUBEFLOW_JUPYTER = kubeflow-registry.default.svc.cluster.local:30000/kubeflow:$(IMAGE_TAG)

IMAGE_SPE = $(DOCKER_REGISTRY)/utils/sentencepiece:$(IMAGE_TAG)
IMAGE_MECAB = $(DOCKER_REGISTRY)/utils/mecab:$(IMAGE_TAG)
IMAGE_GLOVE = $(DOCKER_REGISTRY)/utils/glove:$(IMAGE_TAG)
IMAGE_KONLPY = $(DOCKER_REGISTRY)/utils/konlpy:$(IMAGE_TAG)
IMAGE_KHAIII = $(DOCKER_REGISTRY)/utils/khaiii:$(IMAGE_TAG)
IMAGE_FASTTEXT = $(DOCKER_REGISTRY)/utils/fast_text:$(IMAGE_TAG)

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
MIRROR =

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
all: start-minio mk-bucket utils base batch stop-minio
batch: mlflow kubeflow dev
utils: sentencepiece konlpy glove fastText khaiii mecab

inst-minio-client:
	wget https://dl.min.io/client/mc/release/linux-amd64/mc
	chmod +x mc 
	sudo mv mc /usr/bin/ 

start-minio:
	docker run \
		-d \
		--name minio \
		-p 9000:9000 \
		-v $(shell pwd)/.cache:/data:rw \
		-e "MINIO_ACCESS_KEY=$(MINIO_ACCESS_KEY)" \
		-e "MINIO_SECRET_KEY=$(MINIO_SECRET_KEY)" \
		minio/minio server /data

.ONESHELL:
mk-bucket:
	mc alias set $(MINIO_BUCKET) ${MINIO_URI} ${MINIO_ACCESS_KEY} ${MINIO_SECRET_KEY}
	mc mb $(MINIO_BUCKET)/$(MINIO_PATH)

stop-minio:
	docker stop minio
	docker rm minio

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
	
	docker save $(IMAGE_BASE) | gzip - > base.$(IMAGE_TAG).tar.gz

.ONESHELL:
kubeflow:
	cd docker/kubeflow/
	docker build $(MIRROR) $(DOCKER_LABEL) \
		--build-arg "BASE_IMAGE=$(IMAGE_BASE)" \
		-t $(IMAGE_KUBEFLOW) \
		.

	docker tag $(IMAGE_KUBEFLOW) $(IMAGE_KUBEFLOW_JUPYTER)
	docker save $(IMAGE_KUBEFLOW) | gzip - > kubeflow.$(IMAGE_TAG).tar.gz

.ONESHELL:
mlflow:
	cd docker/mlflow/
	docker build $(MIRROR) $(DOCKER_LABEL) \
		--build-arg "BASE_IMAGE=$(IMAGE_BASE)" \
		-t $(IMAGE_MLFLOW) \
		.

	docker save $(IMAGE_MLFLOW) | gzip - > mlflow.$(IMAGE_TAG).tar.gz

.ONESHELL:
dev:
	cd docker/dev/
	docker build $(MIRROR) $(MINIO) $(DOCKER_LABEL) \
		--build-arg "BASE_IMAGE=$(IMAGE_BASE)" \
		-t $(IMAGE_DEV)	\
		.

	docker save $(IMAGE_DEV) | gzip - > dev.$(IMAGE_TAG).tar.gz

.ONESHELL:
push:
	docker push $(IMAGE_DEV)
	docker push $(IMAGE_KUBEFLOW)
	docker push $(IMAGE_KUBEFLOW_JUPYTER)

.ONESHELL:
run-dev:
	docker run \
		-d \
		--hostname dev \
		--name dev \
		-p 8888:8888 \
		-v $(shell pwd):/home/jovyan \
		$(IMAGE_DEV)

.ONESHELL:
shell:
	docker exec -it embedding zsh

.ONESHELL:
clean-utils:
	docker rmi $(IMAGE_SPE)
	docker rmi $(IMAGE_MECAB)
	docker rmi $(IMAGE_GLOVE)
	docker rmi $(IMAGE_KONLPY)
	docker rmi $(IMAGE_KHAIII)
	docker rmi $(IMAGE_FASTTEXT)

.ONESHELL:
git-tag:
	git tag -a 1 -m 'version 1'
