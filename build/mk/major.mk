
major-start:
	IMAGE=$(IMAGE):$(IMAGE_TAG) \
	MQ_HOSTS=$(MQ_HOSTS) \
	CRAWLER_OPT="$(CRAWLER_OPT)" \
		docker-compose --project-directory major-press -f $(YAML_DIR)/major-press.yml up -d

major-stop:
	IMAGE=$(IMAGE):$(IMAGE_TAG) \
	MQ_HOSTS=$(MQ_HOSTS) \
	CRAWLER_OPT="$(CRAWLER_OPT)" \
		docker-compose --project-directory major-press -f $(YAML_DIR)/major-press.yml down

major-logs:
	IMAGE=$(IMAGE):$(IMAGE_TAG) \
	MQ_HOSTS=$(MQ_HOSTS) \
	CRAWLER_OPT="$(CRAWLER_OPT)" \
		docker-compose --project-directory major-press -f $(YAML_DIR)/major-press.yml logs -f

