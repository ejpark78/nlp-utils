
.ONESHELL:
base:
	docker build \
		-t $(BASE_IMAGE) \
		-f base/Dockerfile \
		--add-host "corpus.ncsoft.com:172.20.79.241" \
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
		--exclude=*.pycharm* \
		--exclude=__pycache__ \
		--exclude=build \
		--exclude=data \
		--exclude=notebook \
		--exclude=wrap \
		--exclude=venv \
		--exclude=tmp \
		--exclude=module/selenium-data \
		.

	cd build/
	docker build \
		-t $(IMAGE_NAME) \
		-f Dockerfile \
		--build-arg BASE_IMAGE=$(BASE_IMAGE) \
		--add-host "corpus.ncsoft.com:172.20.79.241" \
		.

	rm app.tar.gz

pull:
	docker pull $(IMAGE_NAME)

push:
	docker push $(IMAGE_NAME)
