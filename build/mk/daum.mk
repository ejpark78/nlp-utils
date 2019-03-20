
daum:
	docker pull $(IMAGE_NAME)
	docker-compose --project-directory daum -f $(YAML_DIR)/daum.yml down
	docker-compose --project-directory daum -f $(YAML_DIR)/daum.yml up -d

stop-daum:
	docker-compose --project-directory daum -f $(YAML_DIR)/daum.yml down

logs-daum:
	docker-compose --project-directory daum -f $(YAML_DIR)/daum.yml logs -f
