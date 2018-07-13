
VERSION = 1.0
DOCKER_REGISTRY = gollum12:5000
IMAGE_NAME = $(DOCKER_REGISTRY)/crawler:$(VERSION)

default: build

.PHONY: build push clean run

.ONESHELL:
build: 
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
		--add-host="koala:172.20.79.85" \
		--name crawler \
		$(IMAGE_NAME)

clean:
	docker system prune -f
