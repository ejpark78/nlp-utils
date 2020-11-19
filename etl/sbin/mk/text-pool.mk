
#HOME_DIR = ../../..
#
#ELASTIC_HOST = http://corpus.ncsoft.com:9200
#ELASTIC_HOST_DMZ = http://localhost:19200
#
#WORK_DIR = $(shell date -I)
#
#SBIN_DIR = $(HOME_DIR)/sbin/text_pool
#
#BBS_FILE = ../bbs/3rd_2019-03/bbs-lineagem.json.bz2

.PHONY: *

# 게시판 분리
.ONESHELL:
split-bbs:
	echo "게시판 분리"
	mkdir -p $(WORK_DIR)/bbs
	time $(SBIN_DIR)/split.sh $(BBS_FILE) $(WORK_DIR)/bbs

# 게시판 단위 형태소 분석
# 분석 실행
.ONESHELL:
bbs:
	time parallel -j 10 -k --bar -a $(WORK_DIR)/bbs/file.list \
		$(SBIN_DIR)/batch-bbs.sh $(HOME_DIR) corpus_process-bbs-lineagem {} $(HOSTS_DIR)/game.list

# 텍스트 추출
.ONESHELL:
bbs2text:
	echo "텍스트 추출"
	time parallel -j 10 -k --bar -a $(WORK_DIR)/bbs/file.list \
		$(SBIN_DIR)/bbs2pkl.sh $(HOME_DIR) {} {}.pkl "free"

	echo "텍스트 추출 결과 병합: 중복 제거"
	time python3 $(HOME_DIR)/lineagem_utils.py -merge -filename $(WORK_DIR)/tmp \
		| pbzip2 > $(WORK_DIR)/text-bbs.json.bz2

# 텍스트 분리
.ONESHELL:
split-text:
	time $(SBIN_DIR)/split.sh $(WORK_DIR)/text-bbs.json.bz2 $(WORK_DIR)/bbs_parted
	time $(SBIN_DIR)/split.sh ../chatting/chatting-log.2019-03-12.json.bz2 $(WORK_DIR)/chatting_parted

# 분석 실행
.ONESHELL:
bbs-text:
	time parallel -j 10 -k --bar -a bbs_parted/file.list \
		$(SBIN_DIR)/batch-text.sh bbs {} $(HOSTS_DIR)/game.list

.ONESHELL:
chatting-text:
	time parallel -j 10 -k --bar -a chatting_parted/file.list \
		$(SBIN_DIR)/batch-text.sh chatting {} $(HOSTS_DIR)/game.list

# 결과 취합
.ONESHELL:
sync:
	rm -rf merge
	time parallel -j 10 -k --bar -a $(HOSTS_DIR)/game.list \
		$(SBIN_DIR)/sync.sh {} $(WORK_DIR)/merge && sync

.ONESHELL:
merge:
	echo "bbs text 추출"
	time parallel -j 10 -k --bar -a $(HOSTS_DIR)/game.list \
		$(SBIN_DIR)/merge.sh {} $(WORK_DIR)/merge bbs && sync
	time pbzip2 -c -d $(WORK_DIR)/merge/??.bbs.json.bz2 | bzip2 > ${WORK_DIR}/bbs.json.bz2 && sync

	echo "chatting text 추출"
	time parallel -j 10 -k --bar -a $(HOSTS_DIR)/game.list \
		$(SBIN_DIR)/merge.sh {} $(WORK_DIR)/merge chatting && sync
	time pbzip2 -c -d $(WORK_DIR)/merge/??.chatting.json.bz2 | bzip2 > ${WORK_DIR}/chatting.json.bz2 && sync

# 통계 정보 추출
.ONESHELL:
stats:
	time $(SBIN_DIR)/stats.sh bbs.json.bz2 bbs.txt.bz2 bbs.count.txt
	time $(SBIN_DIR)/stats.sh chatting.json.bz2 chatting.txt.bz2 chatting.count.txt

# 분석 결과를 elasticsearch에 입력한다.
.ONESHELL:
insert-text:
	time python3 $(HOME_DIR)/lineagem_utils.py \
		-import_data \
		-host $(ELASTIC_HOST) \
		-index text-bbs-lineagem \
		-mapping $(HOME_DIR)/http/mapping/text-lineagem.json \
		-filename $(today)/bbs.json.bz2

	time python3 $(HOME_DIR)/lineagem_utils.py \
		-import_data \
		-host $(ELASTIC_HOST) \
		-index text-chatting-lineagem \
		-mapping $(HOME_DIR)/http/mapping/text-lineagem.json \
		-filename $(today)/chatting.json.bz2

# 정리
.ONESHELL:
clean:
	time parallel -j 10 -k --bar -a $(HOSTS_DIR)/game.list \
		$(SBIN_DIR)/clenup.sh {} $(DATA_DIR)
