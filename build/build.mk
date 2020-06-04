
# image
BASE_IMAGE = corpus:5000/base/crawler:latest

IMAGE = corpus:5000/crawler
#IMAGE_TAG = $(shell date +%F.%H)
#IMAGE_TAG = $(shell git rev-parse --short HEAD)
IMAGE_TAG = $(shell git describe --tags --long | cut -f1,2 -d'-' | tr '-' '.').$(shell git rev-list --count HEAD)

# Mirror
APT_CODE_NAME = focal
APT_MIRROR = http://corpus.ncsoft.com:8081/repository/$(APT_CODE_NAME)/
PIP_MIRROR = http://pip:nlplab@corpus.ncsoft.com:8081/repository/pypi/simple
PIP_TRUST_HOST = corpus.ncsoft.com

#APT_MIRROR = http://hq-lx-repo.korea.ncsoft.corp/ubuntu/
#PIP_MIRROR = http://mirror.kakao.com/pypi/simple
#PIP_TRUST_HOST = mirror.kakao.com

.ONESHELL:
base:
	docker build \
		-t $(BASE_IMAGE) \
		-f base/Dockerfile \
		--add-host "corpus.ncsoft.com:172.20.93.112" \
		--build-arg "APT_MIRROR=$(APT_MIRROR)" \
		--build-arg "APT_CODE_NAME=$(APT_CODE_NAME)" \
		--build-arg "PIP_TRUST_HOST=$(PIP_TRUST_HOST)" \
		--build-arg "PIP_MIRROR=$(PIP_MIRROR)" \
		.

.ONESHELL:
build:
	cd ../
	tar cvfz ./build/app.tar.gz \
		--exclude=.git \
		--exclude=.pki \
		--exclude=.idea \
		--exclude=.cache \
		--exclude=.vscode \
		--exclude=.ipynb_checkpoints \
		--exclude=*.log \
		--exclude=*.tar.gz \
		--exclude=*.bz2 \
		--exclude=*.pycharm* \
		--exclude=__pycache__ \
		--exclude=tmp \
		--exclude=log \
		--exclude=wrap \
		--exclude=venv \
		--exclude=data \
		--exclude=down \
		--exclude=build \
		--exclude=status \
		--exclude=notebook \
		--exclude=cache \
		.

	cd build/
	docker build \
		-t $(IMAGE):$(IMAGE_TAG) \
		-f Dockerfile \
		--build-arg BASE_IMAGE=$(BASE_IMAGE) \
		--build-arg "APT_MIRROR=$(APT_MIRROR)" \
		--build-arg "APT_CODE_NAME=$(APT_CODE_NAME)" \
		--build-arg "PIP_TRUST_HOST=$(PIP_TRUST_HOST)" \
		--build-arg "PIP_MIRROR=$(PIP_MIRROR)" \
		--label "app=crawler" \
		--label "version=$(IMAGE_TAG)" \
		--label "image_name=$(IMAGE)" \
		--label "build-date=$(shell date +'%Y-%m-%d %H:%M:%S')" \
		--label "git.branch=$(shell git rev-parse --abbrev-ref HEAD)" \
		--label "git.tag=$(shell git describe --tags --long)" \
		--label "git.commit.id=$(shell git rev-parse --short HEAD)" \
		--label "git.commit.count=$(shell git rev-list --count HEAD)" \
		--add-host "corpus.ncsoft.com:172.20.93.112" \
		.

	docker tag $(IMAGE):$(IMAGE_TAG) $(IMAGE):latest

	rm app.tar.gz

.ONESHELL:
pull:
	docker pull $(IMAGE):$(IMAGE_TAG)
	docker pull $(IMAGE):latest

	source $(ENV_FILE)

	docker pull $$CRAWLER_IMAGE
	docker pull $$CORPUS_PROCESSOR_IMAGE

.ONESHELL:
push:
	docker push $(IMAGE):$(IMAGE_TAG)
	docker push $(IMAGE):latest
