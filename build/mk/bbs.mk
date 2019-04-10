
bbs-start:
	IMAGE=$(IMAGE):$(IMAGE_TAG) \
	MQ_HOSTS=$(MQ_HOSTS) \
	CRAWLER_OPT="$(CRAWLER_OPT)" \
		docker-compose --project-directory bbs -f $(YAML_DIR)/bbs.yml up -d

bbs-stop:
	IMAGE=$(IMAGE):$(IMAGE_TAG) \
	MQ_HOSTS=$(MQ_HOSTS) \
	CRAWLER_OPT="$(CRAWLER_OPT)" \
		docker-compose --project-directory bbs -f $(YAML_DIR)/bbs.yml down

bbs-logs:
	IMAGE=$(IMAGE):$(IMAGE_TAG) \
	MQ_HOSTS=$(MQ_HOSTS) \
	CRAWLER_OPT="$(CRAWLER_OPT)" \
		docker-compose --project-directory bbs -f $(YAML_DIR)/bbs.yml logs -f
