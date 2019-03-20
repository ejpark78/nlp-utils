
naver-kin:
	docker pull $(IMAGE_NAME)
	docker-compose --project-directory naver-kin -f $(YAML_DIR)/naver-kin.yml down
	docker-compose --project-directory naver-kin -f $(YAML_DIR)/naver-kin.yml up -d
	docker-compose --project-directory naver-kin -f $(YAML_DIR)/naver-kin.yml logs -f

naver:
	docker pull $(IMAGE_NAME)
	docker-compose --project-directory naver -f $(YAML_DIR)/naver.yml down
	docker-compose --project-directory naver -f $(YAML_DIR)/naver.yml up -d

stop-naver:
	docker-compose --project-directory naver -f $(YAML_DIR)/naver.yml down

logs-naver:
	docker-compose --project-directory naver -f $(YAML_DIR)/naver.yml logs -f

