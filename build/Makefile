
MODE =

# path
MK_DIR = mk
YAML_DIR = mk

# 값 고정
SHELL := /bin/bash

RESTART = always
CRAWLER_OPT =
USE_POST_MQ = 1

# etc
COMPOSE_HOST = "-H unix:///var/run/docker.sock"

# 환경 변수 설정
ENV_FILE = common.env

ifeq "$(MODE)" "10lan"
	ENV_FILE = 10lan.env
endif

.PHONY: *

include $(MK_DIR)/build.mk

include $(MK_DIR)/naver.mk
include $(MK_DIR)/nate.mk
include $(MK_DIR)/daum.mk
include $(MK_DIR)/bbs.mk
include $(MK_DIR)/sns.mk
include $(MK_DIR)/paige.mk
include $(MK_DIR)/major-press.mk

include $(MK_DIR)/release.mk

include $(MK_DIR)/10lan.mk

# batch
all-start: paige-start major-start nate-start naver-start daum-start bbs-start sns-start
all-stop: paige-stop major-stop nate-stop naver-stop daum-stop bbs-stop sns-stop
all-logs: paige-logs major-logs nate-logs naver-logs daum-logs bbs-logs sns-logs

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
