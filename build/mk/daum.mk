
DAUM_PRJ = daum
DAUM_YAML = $(YAML_DIR)/daum.yml
DAUM_EX_NAME = crawler.daum

daum-start:
	source $(ENV_FILE)

	RESTART=$(RESTART) \
	CRAWLER_OPT=$(CRAWLER_OPT) \
	USE_POST_MQ=$(USE_POST_MQ) \
	RABBITMQ_EXCHANGE_NAME="$(NAVER_EX_NAME)" \
		docker-compose $(COMPOSE_HOST) -p $(DAUM_PRJ) -f $(DAUM_YAML) up -d

daum-stop:
	source $(ENV_FILE)

	RESTART=$(RESTART) \
	CRAWLER_OPT=$(CRAWLER_OPT) \
	USE_POST_MQ=$(USE_POST_MQ) \
	RABBITMQ_EXCHANGE_NAME="$(NAVER_EX_NAME)" \
		docker-compose $(COMPOSE_HOST) -p $(DAUM_PRJ) -f $(DAUM_YAML) down

daum-logs:
	source $(ENV_FILE)

	RESTART=$(RESTART) \
	CRAWLER_OPT=$(CRAWLER_OPT) \
	USE_POST_MQ=$(USE_POST_MQ) \
	RABBITMQ_EXCHANGE_NAME="$(NAVER_EX_NAME)" \
		docker-compose $(COMPOSE_HOST) -p $(DAUM_PRJ) -f $(DAUM_YAML) logs -f
