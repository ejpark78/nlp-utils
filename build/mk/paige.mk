
PAIGE_PRJ = paige
PAIGE_YAML = $(YAML_DIR)/paige.yml
PAIGE_EX_NAME = crawler.paige

.ONESHELL:
paige-start:
	source $(ENV_FILE)

	RESTART="$(RESTART)" \
	CRAWLER_OPT="$(CRAWLER_OPT)" \
	USE_POST_MQ="$(USE_POST_MQ)" \
	RABBITMQ_EXCHANGE_NAME="$(PAIGE_EX_NAME)" \
		docker-compose $(COMPOSE_HOST) -p $(PAIGE_PRJ) -f $(PAIGE_YAML) up -d

.ONESHELL:
paige-stop:
	source $(ENV_FILE)

	RESTART="$(RESTART)" \
	CRAWLER_OPT="$(CRAWLER_OPT)" \
	USE_POST_MQ="$(USE_POST_MQ)" \
	RABBITMQ_EXCHANGE_NAME="$(PAIGE_EX_NAME)" \
		docker-compose $(COMPOSE_HOST) -p $(PAIGE_PRJ) -f $(PAIGE_YAML) down

.ONESHELL:
paige-logs:
	source $(ENV_FILE)

	RESTART="$(RESTART)" \
	CRAWLER_OPT="$(CRAWLER_OPT)" \
	USE_POST_MQ="$(USE_POST_MQ)" \
	RABBITMQ_EXCHANGE_NAME="$(PAIGE_EX_NAME)" \
		docker-compose $(COMPOSE_HOST) -p $(PAIGE_PRJ) -f $(PAIGE_YAML) logs -f

.ONESHELL:
paige-recrawl:
	source $(ENV_FILE)

	RESTART="$(RESTART)" \
	CRAWLER_OPT="$(CRAWLER_OPT)" \
	USE_POST_MQ="$(USE_POST_MQ)" \
	RABBITMQ_EXCHANGE_NAME="$(PAIGE_EX_NAME)" \
		docker-compose $(COMPOSE_HOST) -p recrawl_$(PAIGE_PRJ) -f $(PAIGE_YAML) up

# make CRAWLER_OPT="-re_crawl -date_range=2019-04-16~2019-04-16 -query_field=date" paige-recrawl

.ONESHELL:
paige-recrawl-logs:
	source $(ENV_FILE)

	RESTART="$(RESTART)" \
	CRAWLER_OPT="$(CRAWLER_OPT)" \
	USE_POST_MQ="$(USE_POST_MQ)" \
	RABBITMQ_EXCHANGE_NAME="$(PAIGE_EX_NAME)" \
		docker-compose $(COMPOSE_HOST) -p recrawl_$(PAIGE_PRJ) -f $(PAIGE_YAML) logs

.ONESHELL:
paige-recrawl-logs-dump:
	mkdir -p tmp

	cd tmp
	for f in $(shell docker ps -a --format='{{.Names}}' | grep _1 | grep -v _mq_); do
		docker logs $$f 2>&1 | bzip2 > $$f.bz2
	done

	tar cvf ../logs-$(shell date -I).tar *
	cd ../
	rm -rf tmp

SCALE_OPT = --scale osen=0 --scale mk=0 --scale joins_live=0 --scale sports_chosun=0 --scale spotvnews=0 --scale yonhapnews=0

.ONESHELL:
paige-up:
	source $(ENV_FILE)

	RESTART="$(RESTART)" \
	CRAWLER_OPT="$(CRAWLER_OPT)" \
	USE_POST_MQ="$(USE_POST_MQ)" \
	RABBITMQ_EXCHANGE_NAME="$(PAIGE_EX_NAME)" \
		docker-compose $(COMPOSE_HOST) -p update_$(PAIGE_PRJ) -f $(PAIGE_YAML) up $(SCALE_OPT)

# make RESTART=no USE_POST_MQ=0 CRAWLER_OPT="-update_parsing_info -date_range=2019-04-01~2019-04-01 -query_field=date" paige-up

