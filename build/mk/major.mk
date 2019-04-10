
major-start:
	IMAGE=$(IMAGE):$(IMAGE_TAG) \
		docker-compose --project-directory major-press -f $(YAML_DIR)/major-press.yml up -d

major-stop:
	IMAGE=$(IMAGE):$(IMAGE_TAG) \
		docker-compose --project-directory major-press -f $(YAML_DIR)/major-press.yml down

major-logs:
	IMAGE=$(IMAGE):$(IMAGE_TAG) \
		docker-compose --project-directory major-press -f $(YAML_DIR)/major-press.yml logs -f

