
nate:
	docker pull $(IMAGE_NAME)
	docker-compose --project-directory nate -f $(YAML_DIR)/nate.yml down
	docker-compose --project-directory nate -f $(YAML_DIR)/nate.yml up -d

stop-nate:
	docker-compose --project-directory nate -f $(YAML_DIR)/nate.yml down

logs-nate:
	docker-compose --project-directory nate -f $(YAML_DIR)/nate.yml logs -f

