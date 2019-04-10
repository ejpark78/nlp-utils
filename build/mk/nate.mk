
nate-start:
	IMAGE=$(IMAGE):$(IMAGE_TAG) \
	MQ_HOSTS=$(MQ_HOSTS) \
	CRAWLER_OPT="$(CRAWLER_OPT)" \
		docker-compose --project-directory nate -f $(YAML_DIR)/nate.yml up -d

nate-stop:
	IMAGE=$(IMAGE):$(IMAGE_TAG) \
	MQ_HOSTS=$(MQ_HOSTS) \
	CRAWLER_OPT="$(CRAWLER_OPT)" \
		docker-compose --project-directory nate -f $(YAML_DIR)/nate.yml down

nate-logs:
	IMAGE=$(IMAGE):$(IMAGE_TAG) \
	MQ_HOSTS=$(MQ_HOSTS) \
	CRAWLER_OPT="$(CRAWLER_OPT)" \
		docker-compose --project-directory nate -f $(YAML_DIR)/nate.yml logs -f

