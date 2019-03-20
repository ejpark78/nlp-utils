
bbs:
	docker pull $(IMAGE_NAME)
	docker-compose --project-directory bbs -f $(YAML_DIR)/bbs.yml down
	docker-compose --project-directory bbs -f $(YAML_DIR)/bbs.yml up -d

stop-bbs:
	docker-compose --project-directory bbs -f $(YAML_DIR)/bbs.yml down

logs-bbs:
	docker-compose --project-directory bbs -f $(YAML_DIR)/bbs.yml logs -f
