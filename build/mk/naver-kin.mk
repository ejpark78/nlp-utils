
NAVER_KIN_PRJ = naver-kin
NAVER_KIN_YAML = $(YAML_DIR)/naver-kin.yml

.ONESHELL:
naver-kin-start:
	source $(ENV_FILE)

	RESTART=$(RESTART) \
	CRAWLER_OPT=$(CRAWLER_OPT) \
	USE_POST_MQ=$(USE_POST_MQ) \
		docker-compose $(COMPOSE_HOST) -p $(NAVER_KIN_PRJ) -f $(NAVER_KIN_YAML) up -d $(SCALE)

.ONESHELL:
naver-kin-stop:
	source $(ENV_FILE)

	RESTART=$(RESTART) \
	CRAWLER_OPT=$(CRAWLER_OPT) \
	USE_POST_MQ=$(USE_POST_MQ) \
		docker-compose $(COMPOSE_HOST) -p $(NAVER_KIN_PRJ) -f $(NAVER_KIN_YAML) down --remove-orphans

.ONESHELL:
naver-kin-logs:
	source $(ENV_FILE)

	RESTART=$(RESTART) \
	CRAWLER_OPT=$(CRAWLER_OPT) \
	USE_POST_MQ=$(USE_POST_MQ) \
		docker-compose $(COMPOSE_HOST) -p $(NAVER_KIN_PRJ) -f $(NAVER_KIN_YAML) logs -f
