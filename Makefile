
VERSION ?= 1.0

IMAGE_NAME ?= crawler

SERVER ?= gollum01

IMAGES ?= docker/images

default: crawler

.PHONY: crawler save load 

# crawler
.ONESHELL:
crawler: 
	tar cvfz ./build/app.tar.gz --exclude=build --exclude=__pycache__ --exclude=language_utils --exclude=data --exclude=notebook --exclude=wrap --exclude=*.jar --exclude=venv --exclude=.git --exclude=.idea --exclude=*.pycharm* --exclude=tmp .
	cd build/
	docker build -t $(IMAGE_NAME):$(VERSION) -f Dockerfile .

# 이미지 배포
push: save load

# 도커 이미지 저장
save:
	echo "이미지 저장: $(IMAGE_NAME):$(VERSION)"
	mkdir -p $(IMAGES)
	docker save $(IMAGE_NAME):$(VERSION) | gzip - > $(IMAGES)/$(IMAGE_NAME).$(VERSION).tar.gz

load:
	echo "이미지 업로드: $(IMAGES)/$(IMAGE_NAME).$(VERSION).tar.gz -> $(IMAGE_NAME):$(VERSION)"
	docker -H $(SERVER):2376 load < $(IMAGES)/$(IMAGE_NAME).$(VERSION).tar.gz

clean:
	docker system prune -f
