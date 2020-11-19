
FN = LineageM_BBS_20190306.bak
TBL = TempWorkDB
TBL_LOG = TempWorkDB_log

USER_NAME = SA
USER_PW = nlpLab2018!

CONTAINER = mssql
PORT = 1433:1433

HOME_DIR = ../../../..

default: build

.PHONY: push clean run

# MS-SQL 실행
run:
	docker run \
		-d \
		--name $(CONTAINER) \
		-e 'ACCEPT_EULA=Y' \
		-e 'MSSQL_SA_PASSWORD=$(USER_PW)' \
		-p $(PORT) \
		-v /etc/timezone:/etc/timezone:ro \
		-v /etc/localtime:/etc/localtime:ro \
		-v $(PWD)/data:/var/opt/mssql:rw \
		-v $(PWD):/mnt:rw \
		mcr.microsoft.com/mssql/server:latest

stop:
	docker stop $(CONTAINER)
	docker rm $(CONTAINER)

# 테이블 목록 확인
info:
	docker exec -it $(CONTAINER) \
		/opt/mssql-tools/bin/sqlcmd \
			-S localhost -U $(USER_NAME) -P '$(USER_PW)' \
			-Q 'RESTORE FILELISTONLY FROM DISK = "/mnt/$(FN)"' \
				| tr -s ' ' | cut -d ' ' -f 1-2

restore:
	docker exec -it $(CONTAINER) \
		/opt/mssql-tools/bin/sqlcmd \
			-S localhost -U $(USER_NAME) -P '$(USER_PW)' \
			-Q 'RESTORE DATABASE $(TBL) FROM DISK = "/mnt/$(FN)" WITH MOVE "$(TBL)" TO "/var/opt/mssql/data/$(TBL).mdf", MOVE "$(TBL_LOG)" TO "/var/opt/mssql/data/$(TBL_LOG).ldf"'

merge:
	time $(HOME_DIR)/lineagem.py -merge_article | bzip2 > bbs-lineagem.json.bz2

insert:
	time $(HOME_DIR)/lineagem.py \
		-import_data \
		-index bbs-lineagem \
		-filename bbs-lineagem.json.bz2 \
		-mapping $(HOME_DIR)/http/mapping/bbs-lineagem.json

bash:
	docker exec -it $(CONTAINER) /bin/bash
