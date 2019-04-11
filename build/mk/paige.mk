
PAIGE_PRJ = paige
PAIGE_YAML = $(YAML_DIR)/paige.yml
PAIGE_EX_NAME ="crawler.paige" \

paige-start:
	CRAWLER_OPT="$(CRAWLER_OPT)" \
	CRAWLER_IMAGE="$(CRAWLER_IMAGE)" \
	CORPUS_PROCESSOR_IMAGE="$(CORPUS_PROCESSOR_IMAGE)" \
	HTTP_PROXY="$(HTTP_PROXY)" \
	HTTPS_PROXY="$(HTTPS_PROXY)" \
	ELASTIC_HOST="$(ELASTIC_HOST)" \
	RESTART="$(RESTART)" \
	RABBITMQ_USER="$(RABBITMQ_USER)" \
	RABBITMQ_PASS="$(RABBITMQ_PASS)" \
	RABBITMQ_EXCHANGE_NAME="$(PAIGE_EX_NAME)" \
		docker-compose $(COMPOSE_HOST) -p $(PAIGE_PRJ) -f $(PAIGE_YAML) up -d

paige-stop:
	CRAWLER_OPT="$(CRAWLER_OPT)" \
	CRAWLER_IMAGE="$(CRAWLER_IMAGE)" \
	CORPUS_PROCESSOR_IMAGE="$(CORPUS_PROCESSOR_IMAGE)" \
	HTTP_PROXY="$(HTTP_PROXY)" \
	HTTPS_PROXY="$(HTTPS_PROXY)" \
	ELASTIC_HOST="$(ELASTIC_HOST)" \
	RESTART="$(RESTART)" \
	RABBITMQ_USER="$(RABBITMQ_USER)" \
	RABBITMQ_PASS="$(RABBITMQ_PASS)" \
	RABBITMQ_EXCHANGE_NAME="$(PAIGE_EX_NAME)" \
		docker-compose $(COMPOSE_HOST) -p $(PAIGE_PRJ) -f $(PAIGE_YAML) down

paige-logs:
	CRAWLER_OPT="$(CRAWLER_OPT)" \
	CRAWLER_IMAGE="$(CRAWLER_IMAGE)" \
	CORPUS_PROCESSOR_IMAGE="$(CORPUS_PROCESSOR_IMAGE)" \
	HTTP_PROXY="$(HTTP_PROXY)" \
	HTTPS_PROXY="$(HTTPS_PROXY)" \
	ELASTIC_HOST="$(ELASTIC_HOST)" \
	RESTART="$(RESTART)" \
	RABBITMQ_USER="$(RABBITMQ_USER)" \
	RABBITMQ_PASS="$(RABBITMQ_PASS)" \
	RABBITMQ_EXCHANGE_NAME="$(PAIGE_EX_NAME)" \
		docker-compose $(COMPOSE_HOST) -p $(PAIGE_PRJ) -f $(PAIGE_YAML) logs -f

paige-recrawl:
	PRJ_NAME="recrawl" \
	RESTART="no" \
	CRAWLER_OPT="-re_crawl -date_range 2019-01-01~2019-04-11" \
	CRAWLER_IMAGE="$(CRAWLER_IMAGE)" \
	CORPUS_PROCESSOR_IMAGE="$(CORPUS_PROCESSOR_IMAGE)" \
	HTTP_PROXY="http_proxy=" \
	HTTPS_PROXY="https_proxy=" \
	ELASTIC_HOST="$(ELASTIC_HOST)" \
	RABBITMQ_USER="$(RABBITMQ_USER)" \
	RABBITMQ_PASS="$(RABBITMQ_PASS)" \
	RABBITMQ_EXCHANGE_NAME="$(PAIGE_EX_NAME)" \
		docker-compose $(COMPOSE_HOST) -p $(PAIGE_PRJ) -f $(PAIGE_YAML) up
