
.ONESHELL:
debug:
	docker run \
		-it \
		--user crawler \
		--hostname crawler_debug \
		--entrypoint /bin/bash \
		--add-host "corpus.ncsoft.com:172.20.93.112" \
		--volume ${PWD}/..:/usr/local/app:rw \
		--dns=8.8.8.8 \
		--dns=8.8.4.4 \
		--dns=172.20.0.87 \
		--dns=172.20.0.88 \
		--env HOME=/usr/local/app \
		$(IMAGE):latest
