
sns:
	docker pull $(IMAGE_NAME)
	docker-compose --project-directory sns -f $(YAML_DIR)/sns.yml down
	docker-compose --project-directory sns -f $(YAML_DIR)/sns.yml up -d

stop-sns:
	docker-compose --project-directory sns -f $(YAML_DIR)/sns.yml down

logs-sns:
	docker-compose --project-directory sns -f $(YAML_DIR)/sns.yml logs -f
