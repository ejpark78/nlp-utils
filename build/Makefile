
VERSION = 1.0
DOCKER_REGISTRY = nlpapi:5000
CONTAINER = crawler

BASE_IMAGE = base/crawler:$(VERSION)
IMAGE_NAME = $(DOCKER_REGISTRY)/crawler:$(VERSION)

default: build

.PHONY: base build push clean run

.ONESHELL:
base:
	rm app.tar.gz
	cp ../requirements.txt ./
	docker build -t $(BASE_IMAGE) -f Dockerfile.base .

.ONESHELL:
build:
	cd ../
	tar cvfz ./build/app.tar.gz \
		--exclude=.git \
		--exclude=.idea \
		--exclude=.vscode \
		--exclude=*.jar \
		--exclude=*.tar.gz \
		--exclude=*.pycharm* \
		--exclude=__pycache__ \
		--exclude=build \
		--exclude=data \
		--exclude=notebook \
		--exclude=wrap \
		--exclude=venv \
		--exclude=tmp \
		.

	cd build/
	docker build \
		-t $(IMAGE_NAME) \
		-f Dockerfile \
		.

#		--build-arg BASE_IMAGE=$(BASE_IMAGE) \

push: 
	docker push $(IMAGE_NAME)

run: 
	docker run \
		-it --rm \
		--user crawler \
		-v /etc/hosts:/etc/hosts:ro \
		--name $(CONTAINER) \
		$(IMAGE_NAME)

test: 
	docker run \
		-it --rm \
		-v /etc/hosts:/etc/hosts:ro \
		-v $(PWD)/..:/usr/local/app \
		--name $(CONTAINER) \
		$(IMAGE_NAME)

bash: 
	docker exec -it $(CONTAINER) /bin/bash

clean:
	docker system prune -f
