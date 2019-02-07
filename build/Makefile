
VERSION = 2.0
DOCKER_REGISTRY = nlpapi:5000
CONTAINER = crawler

BASE_IMAGE = base/crawler:latest
IMAGE_NAME = $(DOCKER_REGISTRY)/crawler:$(VERSION)

default: build

.PHONY: base build push clean run

.ONESHELL:
base:
	rm app.tar.gz
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

push: 
	docker push $(IMAGE_NAME)

run: 
	docker run \
		-it --rm \
		--user crawler \
		--name $(CONTAINER) \
		-v /etc/hosts:/etc/hosts:ro \
		-v /etc/timezone:/etc/timezone:ro \
		-v /etc/localtime:/etc/localtime:ro \
		$(IMAGE_NAME)

test: 
	docker run \
		-it --rm \
		-v /etc/hosts:/etc/hosts:ro \
		-v $(PWD)/..:/usr/local/app \
		--name $(CONTAINER) \
		$(IMAGE_NAME)

major-press:
	docker pull $(IMAGE_NAME)
	docker-compose --project-directory major-press -f major-press.yml down
	docker-compose --project-directory major-press -f major-press.yml up -d
	docker-compose --project-directory major-press -f major-press.yml logs -f

naver-kin:
	docker pull $(IMAGE_NAME)
	docker-compose --project-directory naver-kin -f naver-kin.yml down
	docker-compose --project-directory naver-kin -f naver-kin.yml up -d
	docker-compose --project-directory naver-kin -f naver-kin.yml logs -f

naver:
	docker pull $(IMAGE_NAME)
	docker-compose --project-directory naver -f naver.yml down
	docker-compose --project-directory naver -f naver.yml up -d
	docker-compose --project-directory naver -f naver.yml logs -f

nate:
	docker pull $(IMAGE_NAME)
	docker-compose --project-directory nate -f nate.yml down
	docker-compose --project-directory nate -f nate.yml up -d
	docker-compose --project-directory nate -f nate.yml logs -f

daum:
	docker pull $(IMAGE_NAME)
	docker-compose --project-directory daum -f daum.yml down
	docker-compose --project-directory daum -f daum.yml up -d
	docker-compose --project-directory daum -f daum.yml logs -f

bbs:
	docker pull $(IMAGE_NAME)
	docker-compose --project-directory bbs -f bbs.yml down
	docker-compose --project-directory bbs -f bbs.yml up -d
	docker-compose --project-directory bbs -f bbs.yml logs -f

sns:
	docker pull $(IMAGE_NAME)
	docker-compose --project-directory sns -f sns.yml down
	docker-compose --project-directory sns -f sns.yml up -d
	docker-compose --project-directory sns -f sns.yml logs -f

clean:
	docker system prune -f

ps:
	ssh g1 'hostname && docker ps -a --format "table {{.ID}}\t{{.Image}}\t{{.Names}}\t{{.Status}}"'
	ssh g2 'hostname && docker ps -a --format "table {{.ID}}\t{{.Image}}\t{{.Names}}\t{{.Status}}"'
	ssh g3 'hostname && docker ps -a --format "table {{.ID}}\t{{.Image}}\t{{.Names}}\t{{.Status}}"'
	ssh g4 'hostname && docker ps -a --format "table {{.ID}}\t{{.Image}}\t{{.Names}}\t{{.Status}}"'
	ssh g5 'hostname && docker ps -a --format "table {{.ID}}\t{{.Image}}\t{{.Names}}\t{{.Status}}"'
	ssh g6 'hostname && docker ps -a --format "table {{.ID}}\t{{.Image}}\t{{.Names}}\t{{.Status}}"'
#	ssh g7 'hostname && docker ps -a --format "table {{.ID}}\t{{.Image}}\t{{.Names}}\t{{.Status}}"'

