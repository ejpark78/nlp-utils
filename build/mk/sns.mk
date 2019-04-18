
SNS_PRJ = sns
SNS_YAML = $(YAML_DIR)/sns.yml
SNS_EX_NAME = crawler.sns

.ONESHELL:
sns-start:
	source $(ENV_FILE)

	RESTART=$(RESTART) \
	CRAWLER_OPT=$(CRAWLER_OPT) \
	USE_POST_MQ=$(USE_POST_MQ) \
	RABBITMQ_EXCHANGE_NAME="$(SNS_EX_NAME)" \
		docker-compose $(COMPOSE_HOST) -p $(SNS_PRJ) -f $(SNS_YAML) up -d

.ONESHELL:
sns-stop:
	source $(ENV_FILE)

	RESTART=$(RESTART) \
	CRAWLER_OPT=$(CRAWLER_OPT) \
	USE_POST_MQ=$(USE_POST_MQ) \
	RABBITMQ_EXCHANGE_NAME="$(SNS_EX_NAME)" \
		docker-compose $(COMPOSE_HOST) -p $(SNS_PRJ) -f $(SNS_YAML) down

.ONESHELL:
sns-logs:
	source $(ENV_FILE)

	RESTART=$(RESTART) \
	CRAWLER_OPT=$(CRAWLER_OPT) \
	USE_POST_MQ=$(USE_POST_MQ) \
	RABBITMQ_EXCHANGE_NAME="$(SNS_EX_NAME)" \
		docker-compose $(COMPOSE_HOST) -p $(SNS_PRJ) -f $(SNS_YAML) logs -f
