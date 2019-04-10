
naver-kin:
	docker-compose --project-directory naver-kin -f $(YAML_DIR)/naver-kin.yml down
	docker-compose --project-directory naver-kin -f $(YAML_DIR)/naver-kin.yml up -d
	docker-compose --project-directory naver-kin -f $(YAML_DIR)/naver-kin.yml logs -f

naver-start:
	IMAGE=$(IMAGE):$(IMAGE_TAG) \
	MQ_HOSTS=$(MQ_HOSTS) \
	CRAWLER_OPT="$(CRAWLER_OPT)" \
		docker-compose --project-directory naver -f $(YAML_DIR)/naver.yml up -d

naver-stop:
	IMAGE=$(IMAGE):$(IMAGE_TAG) \
	MQ_HOSTS=$(MQ_HOSTS) \
	CRAWLER_OPT="$(CRAWLER_OPT)" \
		docker-compose --project-directory naver -f $(YAML_DIR)/naver.yml down

naver-logs:
	IMAGE=$(IMAGE):$(IMAGE_TAG) \
	MQ_HOSTS=$(MQ_HOSTS) \
	CRAWLER_OPT="$(CRAWLER_OPT)" \
		docker-compose --project-directory naver -f $(YAML_DIR)/naver.yml logs -f
