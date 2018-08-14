
VERSION = 1.0
DOCKER_REGISTRY = nlpapi:5000
CONTAINER = crawler
IMAGE_NAME = $(DOCKER_REGISTRY)/crawler:$(VERSION)

default: build

.PHONY: build push clean run

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
	docker build -t $(IMAGE_NAME) -f Dockerfile .

push: 
	docker push $(IMAGE_NAME)

run: 
	docker run \
		-it --rm \
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

sh: 
	docker exec -it $(CONTAINER) /bin/sh

clean:
	docker system prune -f
