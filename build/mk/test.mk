
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
