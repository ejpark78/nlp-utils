
# image
BASE_IMAGE = corpus:5000/base/crawler:latest

IMAGE = corpus:5000/crawler
IMAGE_TAG = $(shell date +%F.%H)

# Mirror
APT_MIRROR = http://corpus.ncsoft.com:8081/repository/ubuntu/
PIP_MIRROR = http://corpus.ncsoft.com:8081/repository/pypi/simple
PIP_TRUST_HOST = corpus.ncsoft.com

.ONESHELL:
base:
	docker build \
		-t $(BASE_IMAGE) \
		-f base/Dockerfile \
		--add-host "corpus.ncsoft.com:172.20.93.112" \
		--build-arg "APT_MIRROR=$(APT_MIRROR)" \
		--build-arg "PIP_TRUST_HOST=$(PIP_TRUST_HOST)" \
		--build-arg "PIP_MIRROR=$(PIP_MIRROR)" \
		.

.ONESHELL:
build:
	cd ../
	tar cvfz ./build/app.tar.gz \
		--exclude=.git \
		--exclude=.idea \
		--exclude=.vscode \
		--exclude=*.jar \
		--exclude=*.tar.gz \
		--exclude=*.bz2 \
		--exclude=*.pycharm* \
		--exclude=__pycache__ \
		--exclude=build \
		--exclude=data \
		--exclude=notebook \
		--exclude=wrap \
		--exclude=venv \
		--exclude=tmp \
		--exclude=status \
		--exclude=module/selenium-data \
		.

	cd build/
	docker build \
		-t $(IMAGE):$(IMAGE_TAG) \
		-f Dockerfile \
		--build-arg BASE_IMAGE=$(BASE_IMAGE) \
		--label "app=crawler" \
		--label "version=$(IMAGE_TAG)" \
		--label "image_name=$(IMAGE)" \
		--label "build-date=$(shell date +'%Y-%m-%d %H:%M:%S')" \
		--label "git.commit_id=$(shell git rev-parse HEAD)" \
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
