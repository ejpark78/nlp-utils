
sns-start:
	IMAGE=$(IMAGE):$(IMAGE_TAG) \
		docker-compose --project-directory sns -f $(YAML_DIR)/sns.yml up -d

sns-stop:
	IMAGE=$(IMAGE):$(IMAGE_TAG) \
		docker-compose --project-directory sns -f $(YAML_DIR)/sns.yml down

sns-logs:
	IMAGE=$(IMAGE):$(IMAGE_TAG) \
		docker-compose --project-directory sns -f $(YAML_DIR)/sns.yml logs -f
