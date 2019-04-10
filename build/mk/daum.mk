
daum-start:
	IMAGE=$(IMAGE):$(IMAGE_TAG) \
		docker-compose --project-directory daum -f $(YAML_DIR)/daum.yml up -d

daum-stop:
	IMAGE=$(IMAGE):$(IMAGE_TAG) \
		docker-compose --project-directory daum -f $(YAML_DIR)/daum.yml down

daum-logs:
	IMAGE=$(IMAGE):$(IMAGE_TAG) \
		docker-compose --project-directory daum -f $(YAML_DIR)/daum.yml logs -f
