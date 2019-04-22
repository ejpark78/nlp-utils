
MAJOR_PRESS_PRJ = major
MAJOR_PRESS_YAML = $(YAML_DIR)/major-press.yml
MAJOR_PRESS_EX_NAME = crawler.major_press

.ONESHELL:
major-start:
	source $(ENV_FILE)

	RESTART=$(RESTART) \
	CRAWLER_OPT=$(CRAWLER_OPT) \
	USE_POST_MQ=$(USE_POST_MQ) \
	RABBITMQ_EXCHANGE_NAME="$(MAJOR_PRESS_EX_NAME)" \
		docker-compose $(COMPOSE_HOST) -p $(MAJOR_PRESS_PRJ) -f $(MAJOR_PRESS_YAML) up -d

.ONESHELL:
major-stop:
	source $(ENV_FILE)

	RESTART=$(RESTART) \
	CRAWLER_OPT=$(CRAWLER_OPT) \
	USE_POST_MQ=$(USE_POST_MQ) \
	RABBITMQ_EXCHANGE_NAME="$(MAJOR_PRESS_EX_NAME)" \
		docker-compose $(COMPOSE_HOST) -p $(MAJOR_PRESS_PRJ) -f $(MAJOR_PRESS_YAML) down

.ONESHELL:
major-logs:
	source $(ENV_FILE)

	RESTART=$(RESTART) \
	CRAWLER_OPT=$(CRAWLER_OPT) \
	USE_POST_MQ=$(USE_POST_MQ) \
	RABBITMQ_EXCHANGE_NAME="$(MAJOR_PRESS_EX_NAME)" \
		docker-compose $(COMPOSE_HOST) -p $(MAJOR_PRESS_PRJ) -f $(MAJOR_PRESS_YAML) logs -f

.ONESHELL:
major-up:
	source $(ENV_FILE)

	RESTART=$(RESTART) \
	CRAWLER_OPT=$(CRAWLER_OPT) \
	USE_POST_MQ=$(USE_POST_MQ) \
	RABBITMQ_EXCHANGE_NAME="$(MAJOR_PRESS_EX_NAME)" \
		docker-compose $(COMPOSE_HOST) -p update_$(MAJOR_PRESS_PRJ) -f $(MAJOR_PRESS_YAML) up

# make RESTART=no USE_POST_MQ=0 CRAWLER_OPT="-update_parsing_info -date_range=2019-04-01~2019-04-01 -query_field=date" major-up
# make RESTART=no USE_POST_MQ=0 CRAWLER_OPT="-update_parsing_info" major-up

