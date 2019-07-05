
NAVER_TERMS_PRJ = naver-kin
NAVER_TERMS_YAML = $(YAML_DIR)/naver-terms.yml

.ONESHELL:
naver-terms-start:
	source $(ENV_FILE)

	RESTART=$(RESTART) \
	CRAWLER_OPT=$(CRAWLER_OPT) \
	USE_POST_MQ=$(USE_POST_MQ) \
		docker-compose $(COMPOSE_HOST) -p $(NAVER_TERMS_PRJ) -f $(NAVER_TERMS_YAML) up -d $(SCALE)

.ONESHELL:
naver-terms-stop:
	source $(ENV_FILE)

	RESTART=$(RESTART) \
	CRAWLER_OPT=$(CRAWLER_OPT) \
	USE_POST_MQ=$(USE_POST_MQ) \
		docker-compose $(COMPOSE_HOST) -p $(NAVER_TERMS_PRJ) -f $(NAVER_TERMS_YAML) down --remove-orphans

.ONESHELL:
naver-terms-logs:
	source $(ENV_FILE)

	RESTART=$(RESTART) \
	CRAWLER_OPT=$(CRAWLER_OPT) \
	USE_POST_MQ=$(USE_POST_MQ) \
		docker-compose $(COMPOSE_HOST) -p $(NAVER_TERMS_PRJ) -f $(NAVER_TERMS_YAML) logs -f
