
HOME_DIR = ../../..
SBIN_DIR = $(HOME_DIR)/sbin/text_pool
HOSTS_DIR = $(HOME_DIR)/sbin/hosts
YAML_DIR = $(HOME_DIR)/sbin/yml

# 데몬 실행
up-game:
	time parallel -j 10 -k --bar -a $(HOSTS_DIR)/game.list \
		docker-compose -H {}:2376 -f $(YAML_DIR)/text-game.yml pull

	time parallel -j 10 -k --bar -a $(HOSTS_DIR)/game.list \
		DATA_PATH=$(DATA_DIR) \
			docker-compose -H {}:2376 -f $(YAML_DIR)/text-game.yml up -d --scale game=8

down-game:
	time parallel -j 10 -k --bar -a $(HOSTS_DIR)/game.list \
		docker-compose -H {}:2376 -f $(YAML_DIR)/text-game.yml down --remove-orphans

ps-game:
	time parallel -j 10 -k --bar -a $(HOSTS_DIR)/game.list \
		docker -H {}:2376 ps -a

clean-game:
	time parallel -j 10 -k --bar -a $(HOSTS_DIR)/game.list \
		$(SBIN_DIR)/make.sh corpus-process {} clean

# release
release-game:
	parallel -j 10 -k --bar -a $(HOSTS_DIR)/game.list \
	 	$(SBIN_DIR)/release.sh {} corpus-process

# text-game
down-text-game:
	docker-compose --project-directory text-game -f $(YAML_DIR)/text-game.yml down --remove-orphans

log-text-game:
	docker-compose --project-directory text-game -f $(YAML_DIR)/text-game.yml logs -f

text-game: down-text-game
	docker-compose --project-directory $@ -f $(YAML_DIR)/text-game.yml up -d --scale game=8

# text-game-rest
text-game-rest:
	docker-compose --project-directory $@ -f $(YAML_DIR)/text-game.yml down --remove-orphans
	docker-compose --project-directory $@ -f $(YAML_DIR)/text-game.yml up -d
