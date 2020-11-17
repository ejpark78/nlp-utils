
.PHONY: *

# image
BASE_IMAGE = registry.nlp-utils/base/crawler:latest

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
MIRROR += --add-host "nlp-utils:172.19.153.41"
MIRROR += --build-arg "APT_MIRROR=$(APT_MIRROR)"
MIRROR += --build-arg "APT_CODE_NAME=$(APT_CODE_NAME)"
MIRROR += --build-arg "PIP_MIRROR=$(PIP_MIRROR)"
MIRROR += --build-arg "PIP_TRUST_HOST=$(PIP_TRUST_HOST)"

batch: build push

.ONESHELL:
base:
	docker build \
		$(MIRROR) \
		-t $(BASE_IMAGE) \
		-f base/Dockerfile \
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
		--exclude=*.db \
		--exclude=*.pycharm* \
		--exclude=*browsermob-proxy* \
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
		--exclude=ops \
		.

	cd build/
	docker build \
		-t $(IMAGE):$(IMAGE_TAG) \
		-f Dockerfile \
		--build-arg BASE_IMAGE=$(BASE_IMAGE) \
		--build-arg "docker_image=$(IMAGE):$(IMAGE_TAG)" \
		--build-arg "docker_tag=$(IMAGE_TAG)" \
		--build-arg "build_date='$(BUILD_DATE)'" \
		--build-arg "git_url=$(GIT_URL)" \
		--build-arg "git_branch=$(GIT_BRANCH)" \
		--build-arg "git_tag=$(GIT_TAG)" \
		--build-arg "git_commit_id=$(GIT_COMMIT_ID)" \
		--build-arg "git_commit_count=$(GIT_COMMIT)" \
		--label "app=crawler" \
		--label "version=$(IMAGE_TAG)" \
		--label "image_name=$(IMAGE)" \
		--label "build-date=$(BUILD_DATE)" \
		--label "git.url=$(GIT_URL)" \
		--label "git.branch=$(GIT_BRANCH)" \
		--label "git.tag=$(GIT_TAG)" \
		--label "git.commit.id=$(GIT_COMMIT_ID)" \
		--label "git.commit.count=$(GIT_COMMIT)" \
		--add-host "nlp-utils:172.19.153.41" \
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
		$(BASE_IMAGE)

prune:
	cat /etc/hosts \
		| grep nc-crawler \
		| perl -ple 's/\s+/\t/g' \
		| cut -f2 \
		| xargs -I{} ssh {} "docker system prune -f ; docker image prune -f -a"
