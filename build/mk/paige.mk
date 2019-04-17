
PAIGE_PRJ = paige
PAIGE_YAML = $(YAML_DIR)/paige.yml
PAIGE_EX_NAME = crawler.paige

.ONESHELL:
paige-start:
	source $(ENV_FILE)

	RESTART=$(RESTART) \
	CRAWLER_OPT=$(CRAWLER_OPT) \
	USE_POST_MQ=$(USE_POST_MQ) \
	RABBITMQ_EXCHANGE_NAME="$(NAVER_EX_NAME)" \
		docker-compose $(COMPOSE_HOST) -p $(PAIGE_PRJ) -f $(PAIGE_YAML) up -d

.ONESHELL:
paige-stop:
	source $(ENV_FILE)

	RESTART=$(RESTART) \
	CRAWLER_OPT=$(CRAWLER_OPT) \
	USE_POST_MQ=$(USE_POST_MQ) \
	RABBITMQ_EXCHANGE_NAME="$(NAVER_EX_NAME)" \
		docker-compose $(COMPOSE_HOST) -p $(PAIGE_PRJ) -f $(PAIGE_YAML) down

.ONESHELL:
paige-logs:
	source $(ENV_FILE)

	RESTART=$(RESTART) \
	CRAWLER_OPT=$(CRAWLER_OPT) \
	USE_POST_MQ=$(USE_POST_MQ) \
	RABBITMQ_EXCHANGE_NAME="$(NAVER_EX_NAME)" \
		docker-compose $(COMPOSE_HOST) -p $(PAIGE_PRJ) -f $(PAIGE_YAML) logs -f

.ONESHELL:
paige-recrawl:
	source common.env

	RESTART="no" \
	USE_POST_MQ="0" \
	CRAWLER_OPT="$(CRAWLER_OPT)" \
	RABBITMQ_EXCHANGE_NAME="$(NAVER_EX_NAME)" \
		docker-compose $(COMPOSE_HOST) -p recrawl -f $(PAIGE_YAML) up

.ONESHELL:
paige-recrawl-logs:
	source common.env

	RESTART="no" \
	USE_POST_MQ="0" \
	CRAWLER_OPT="$(CRAWLER_OPT)" \
	RABBITMQ_EXCHANGE_NAME="$(NAVER_EX_NAME)" \
		docker-compose $(COMPOSE_HOST) -p recrawl -f $(PAIGE_YAML) logs
