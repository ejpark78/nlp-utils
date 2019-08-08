
MODE =

# path
MK_DIR = mk
YAML_DIR = mk

# source $(ENV_FILE) 용 고정값
SHELL := /bin/bash

RESTART = always
CRAWLER_OPT =
USE_POST_MQ = 1

#  --scale mlbpark-kbo=0 --scale mlbpark-mlb=0 --scale mlbpark-bullpen=0 --scale lineagem=0
SCALE =

# etc
COMPOSE_HOST = "-H unix:///var/run/docker.sock"

# 환경 변수 설정
ENV_FILE = common.env

.PHONY: *

include $(MK_DIR)/build.mk

include $(MK_DIR)/naver.mk
include $(MK_DIR)/naver-kin.mk
include $(MK_DIR)/naver-terms.mk
include $(MK_DIR)/nate.mk
include $(MK_DIR)/daum.mk
include $(MK_DIR)/bbs.mk
include $(MK_DIR)/sns.mk
include k8s/k8s.mk

include $(MK_DIR)/release.mk

# batch
all-start: nate-start naver-start daum-start bbs-start sns-start
all-stop: nate-stop naver-stop daum-stop bbs-stop sns-stop
all-logs: nate-logs naver-logs daum-logs bbs-logs sns-logs

.ONESHELL:
check-env:
	@source $(ENV_FILE)
	@env | sort

.ONESHELL:
check-ip:
	@echo "Public IP: "
	@curl -s https://ipinfo.io/ip

	@echo "Local IP: "
	@hostname -I
