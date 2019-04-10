
sns-start:
	IMAGE=$(IMAGE):$(IMAGE_TAG) \
	MQ_HOSTS=$(MQ_HOSTS) \
	CRAWLER_OPT="$(CRAWLER_OPT)" \
		docker-compose --project-directory sns -f $(YAML_DIR)/sns.yml up -d

sns-stop:
	IMAGE=$(IMAGE):$(IMAGE_TAG) \
	MQ_HOSTS=$(MQ_HOSTS) \
	CRAWLER_OPT="$(CRAWLER_OPT)" \
		docker-compose --project-directory sns -f $(YAML_DIR)/sns.yml down

sns-logs:
	IMAGE=$(IMAGE):$(IMAGE_TAG) \
	MQ_HOSTS=$(MQ_HOSTS) \
	CRAWLER_OPT="$(CRAWLER_OPT)" \
		docker-compose --project-directory sns -f $(YAML_DIR)/sns.yml logs -f
