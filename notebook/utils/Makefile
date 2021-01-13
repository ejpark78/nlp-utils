

.PHONY: *

.ONESHELL:
run:
	#docker run \
	#    -it \
	#    -v $PWD:/root/server/python/mnt \
	#    -e WORK_DIR=/root/server/python/mnt \
	#    --entrypoint bash \
	#    galadriel02.korea.ncsoft.corp:5000/kmat:latest

	docker run \
		-it \
		--user user \
		--hostname kmt \
		-v $(shell pwd):/home/user/server/python/mnt \
		-e WORK_DIR=/home/user/server/python/mnt \
		-e HOME=/home/user \
		-w /home/user/server/python/mnt \
		--entrypoint bash \
		corpus:5000/contents/mt/pre_process

.ONESHELL:
morp:
	ls -1 AIHub/*.json.bz2 | xargs -I{} ./kmat.sh {}
#	ls -1 dictionary/*.bitext.json.bz2 | xargs -I{} ./kmat.sh {}
#	ls -1 news/*.bitext.json.bz2 | xargs -I{} ./kmat.sh {}
