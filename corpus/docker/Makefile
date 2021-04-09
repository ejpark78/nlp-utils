
.PHONY: *

# image
IMAGE = registry.nlp-utils/corpus

# Mirror
APT_CODE_NAME = focal
APT_MIRROR = https://nlp-utils/repository/$(APT_CODE_NAME)/
PIP_MIRROR = https://k8s:nlplab@nlp-utils/repository/pypi/simple
PIP_TRUST_HOST = nlp-utils

MIRROR =
MIRROR += --build-arg "APT_MIRROR=$(APT_MIRROR)"
MIRROR += --build-arg "APT_CODE_NAME=$(APT_CODE_NAME)"
MIRROR += --build-arg "PIP_MIRROR=$(PIP_MIRROR)"
MIRROR += --build-arg "PIP_TRUST_HOST=$(PIP_TRUST_HOST)"

# APP
APP_INSTALL =
APP_INSTALL += --build-arg "GIT_BRANCH=dev"
APP_INSTALL += --build-arg "GIT_REPO=http://ejpark:2Q9H2fF-E8sPqJXd61GC@galadriel02.korea.ncsoft.corp/crawler-dev/corpus.git"

DOCKER_BUILD_OPT =
DOCKER_BUILD_OPT += --network=host
DOCKER_BUILD_OPT += --add-host "nlp-utils:172.19.153.41"
DOCKER_BUILD_OPT += --add-host "galadriel02.korea.ncsoft.corp:172.20.92.245"

.ONESHELL:
corpus:
	docker build \
		$(MIRROR) \
		$(DOCKER_BUILD_OPT) \
		$(APP_INSTALL) \
		-t $(IMAGE):latest \
		-f Dockerfile \
		.

.ONESHELL:
push-dev:
	docker push $(IMAGE):latest


.ONESHELL:
run:
	docker run \
		-it --rm \
		--name corpus \
		--hostname corpus \
		--network host \
		-e PORT=8889 \
		--add-host "nlp-utils:172.19.153.41" \
		$(IMAGE):latest
