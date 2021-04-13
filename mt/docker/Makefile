
MOSES_BUILD_IMAGE="corpus:5000/mtops/moses:build"
MOSES_IMAGE="corpus:5000/mtops/moses:latest"
OPENNMT_IMAGE="corpus:5000/mtops/opennmt:latest"
PRE_PROCESS_IMAGE="corpus:5000/mtops/pre_process:latest"

.PHONY: *

# moses
.ONESHELL:
build-moses-base:
	cd moses/build

	docker build \
		--add-host "corpus.ncsoft.com:172.20.93.112" \
		-t ${MOSES_BUILD_IMAGE} \
		-f Dockerfile \
		.

.ONESHELL:
build-moses:
	cd ../bin
	tar cvf ../docker-env/moses/train/bin.tar .
	sync

	cd ../docker-env/moses/train

	docker build \
		--add-host "corpus.ncsoft.com:172.20.93.112" \
		--build-arg "BUILD_IMAGE=${MOSES_BUILD_IMAGE}" \
		-t ${MOSES_IMAGE} \
		-f Dockerfile \
		.

	rm bin.tar

.ONESHELL:
push-moses:
	docker push ${MOSES_IMAGE}

run-moses:
	docker run \
        -it \
        --hostname moses \
		--add-host "corpus.ncsoft.com:172.20.93.112" \
		-e CONFIG_HOST="https://corpus.ncsoft.com:9200" \
		-e CONFIG_INDEX="mt_pipeline-config" \
		-e CONFIG_DOC_ID="moses-dictionary_example" \
		-e CONFIG_USER_AUTH="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdXRoIjoiZWxhc3RpYzpubHBsYWIifQ.N1mOJmt5OBA7Ugi-xeBrY0GzFr79u7QQPHNf4EMxV_Q" \
        -w /home/user \
        -v $(realpath $(shell pwd)/../bin):/home/user/bin \
		${MOSES_IMAGE}

# open-nmt
.ONESHELL:
build-opennmt:
	cd ../bin
	tar cvf ../docker-env/opennmt/bin.tar .
	sync

	cd ../docker-env/opennmt

	docker build \
		--add-host "corpus.ncsoft.com:172.20.93.112" \
		-t ${OPENNMT_IMAGE} \
		-f Dockerfile \
		.

	rm bin.tar

.ONESHELL:
push-opennmt:
	docker push ${OPENNMT_IMAGE}

.ONESHELL:
run-opennmt: 
	docker run \
		-it \
		--gpus all \
        --user user \
        --hostname opennmt \
        --network host \
		--add-host "corpus.ncsoft.com:172.20.93.112" \
		-e NVIDIA_VISIBLE_DEVICES=0 \
		-e CONFIG_HOST="https://corpus.ncsoft.com:9200" \
		-e CONFIG_INDEX="mt_pipeline-config" \
		-e CONFIG_DOC_ID="opennmt-dictionary_example" \
		-e CONFIG_USER_AUTH="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdXRoIjoiZWxhc3RpYzpubHBsYWIifQ.N1mOJmt5OBA7Ugi-xeBrY0GzFr79u7QQPHNf4EMxV_Q" \
		-e PORT="32000" \
		-e URL_ROOT="/nmt" \
		-e SERVER_CONFIG="bin/opennmt/server.json" \
        -w /home/user \
        -v $(realpath $(shell pwd)/../bin):/home/user/bin \
		-t ${OPENNMT_IMAGE}

# pre process
.ONESHELL:
build-pre_process:
	cd pre_process

	docker build \
		--add-host "corpus.ncsoft.com:172.20.93.112" \
		-t ${PRE_PROCESS_IMAGE} \
		-f Dockerfile \
		.

.ONESHELL:
run-pre_process:
	docker run \
		-it \
        --user user \
        --hostname pre_process \
		--add-host "corpus.ncsoft.com:172.20.93.112" \
		-v $(realpath $(shell pwd)/../data):/home/user/server/python/mnt \
		-e WORK_DIR=/home/user/server/python/mnt \
		-e HOME=/home/user \
		-w /home/user/server/python/mnt \
		--entrypoint bash \
		-t ${PRE_PROCESS_IMAGE}

.ONESHELL:
push-pre_process:
	docker push ${PRE_PROCESS_IMAGE}
