
major:
	docker pull $(IMAGE_NAME)
	docker-compose --project-directory major-press -f $(YAML_DIR)/major-press.yml down
	docker-compose --project-directory major-press -f $(YAML_DIR)/major-press.yml up -d

stop-major:
	docker-compose --project-directory major-press -f $(YAML_DIR)/major-press.yml down

logs-major:
	docker-compose --project-directory major-press -f $(YAML_DIR)/major-press.yml logs -f

