
DAUM_PRJ = daum
DAUM_YAML = $(YAML_DIR)/daum.yml
DAUM_EX_NAME = crawler.daum

.ONESHELL:
daum-start:
	source $(ENV_FILE)

	RESTART=$(RESTART) \
	CRAWLER_OPT=$(CRAWLER_OPT) \
	USE_POST_MQ=$(USE_POST_MQ) \
	RABBITMQ_EXCHANGE_NAME="$(DAUM_EX_NAME)" \
		docker-compose $(COMPOSE_HOST) -p $(DAUM_PRJ) -f $(DAUM_YAML) up -d $(SCALE)

.ONESHELL:
daum-stop:
	source $(ENV_FILE)

	RESTART=$(RESTART) \
	CRAWLER_OPT=$(CRAWLER_OPT) \
	USE_POST_MQ=$(USE_POST_MQ) \
	RABBITMQ_EXCHANGE_NAME="$(DAUM_EX_NAME)" \
		docker-compose $(COMPOSE_HOST) -p $(DAUM_PRJ) -f $(DAUM_YAML) down --remove-orphans

.ONESHELL:
daum-logs:
	source $(ENV_FILE)

	RESTART=$(RESTART) \
	CRAWLER_OPT=$(CRAWLER_OPT) \
	USE_POST_MQ=$(USE_POST_MQ) \
	RABBITMQ_EXCHANGE_NAME="$(DAUM_EX_NAME)" \
		docker-compose $(COMPOSE_HOST) -p $(DAUM_PRJ) -f $(DAUM_YAML) logs -f
