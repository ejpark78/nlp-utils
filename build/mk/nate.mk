
NATE_PRJ = nate
NATE_YAML = $(YAML_DIR)/nate.yml
NATE_EX_NAME = crawler.nate

.ONESHELL:
nate-start:
	source $(ENV_FILE)

	RESTART=$(RESTART) \
	CRAWLER_OPT=$(CRAWLER_OPT) \
	USE_POST_MQ=$(USE_POST_MQ) \
	RABBITMQ_EXCHANGE_NAME="$(NATE_EX_NAME)" \
		docker-compose $(COMPOSE_HOST) -p $(NATE_PRJ) -f $(NATE_YAML) up -d $(SCALE)

.ONESHELL:
nate-stop:
	source $(ENV_FILE)

	RESTART=$(RESTART) \
	CRAWLER_OPT=$(CRAWLER_OPT) \
	USE_POST_MQ=$(USE_POST_MQ) \
	RABBITMQ_EXCHANGE_NAME="$(NATE_EX_NAME)" \
		docker-compose $(COMPOSE_HOST) -p $(NATE_PRJ) -f $(NATE_YAML) down --remove-orphans

.ONESHELL:
nate-logs:
	source $(ENV_FILE)

	RESTART=$(RESTART) \
	CRAWLER_OPT=$(CRAWLER_OPT) \
	USE_POST_MQ=$(USE_POST_MQ) \
	RABBITMQ_EXCHANGE_NAME="$(NATE_EX_NAME)" \
		docker-compose $(COMPOSE_HOST) -p $(NATE_PRJ) -f $(NATE_YAML) logs -f

