
BBS_PRJ = bbs
BBS_YAML = $(YAML_DIR)/bbs.yml
BBS_EX_NAME = crawler.bbs

.ONESHELL:
bbs-start:
	source $(ENV_FILE)

	RESTART=$(RESTART) \
	CRAWLER_OPT=$(CRAWLER_OPT) \
	USE_POST_MQ=$(USE_POST_MQ) \
	RABBITMQ_EXCHANGE_NAME="$(BBS_EX_NAME)" \
		docker-compose $(COMPOSE_HOST) -p $(BBS_PRJ) -f $(BBS_YAML) up -d $(SCALE)

.ONESHELL:
bbs-stop:
	source $(ENV_FILE)

	RESTART=$(RESTART) \
	CRAWLER_OPT=$(CRAWLER_OPT) \
	USE_POST_MQ=$(USE_POST_MQ) \
	RABBITMQ_EXCHANGE_NAME="$(BBS_EX_NAME)" \
		docker-compose $(COMPOSE_HOST) -p $(BBS_PRJ) -f $(BBS_YAML) down --remove-orphans

.ONESHELL:
bbs-logs:
	source $(ENV_FILE)

	RESTART=$(RESTART) \
	CRAWLER_OPT=$(CRAWLER_OPT) \
	USE_POST_MQ=$(USE_POST_MQ) \
	RABBITMQ_EXCHANGE_NAME="$(BBS_EX_NAME)" \
		docker-compose $(COMPOSE_HOST) -p $(BBS_PRJ) -f $(BBS_YAML) logs -f
