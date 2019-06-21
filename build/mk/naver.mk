
NAVER_PRJ = naver
NAVER_YAML = $(YAML_DIR)/naver.yml
NAVER_EX_NAME = crawler.naver

.ONESHELL:
naver-start:
	source $(ENV_FILE)

	RESTART=$(RESTART) \
	CRAWLER_OPT=$(CRAWLER_OPT) \
	USE_POST_MQ=$(USE_POST_MQ) \
	RABBITMQ_EXCHANGE_NAME="$(NAVER_EX_NAME)" \
		docker-compose $(COMPOSE_HOST) -p $(NAVER_PRJ) -f $(NAVER_YAML) up -d $(SCALE)

.ONESHELL:
naver-stop:
	source $(ENV_FILE)

	RESTART=$(RESTART) \
	CRAWLER_OPT=$(CRAWLER_OPT) \
	USE_POST_MQ=$(USE_POST_MQ) \
	RABBITMQ_EXCHANGE_NAME="$(NAVER_EX_NAME)" \
		docker-compose $(COMPOSE_HOST) -p $(NAVER_PRJ) -f $(NAVER_YAML) down --remove-orphans

.ONESHELL:
naver-logs:
	source $(ENV_FILE)

	RESTART=$(RESTART) \
	CRAWLER_OPT=$(CRAWLER_OPT) \
	USE_POST_MQ=$(USE_POST_MQ) \
	RABBITMQ_EXCHANGE_NAME="$(NAVER_EX_NAME)" \
		docker-compose $(COMPOSE_HOST) -p $(NAVER_PRJ) -f $(NAVER_YAML) logs -f
