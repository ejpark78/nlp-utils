
CONTAINER = crawler

BASE_IMAGE = corpus:5000/base/crawler:latest
IMAGE_NAME = corpus:5000/crawler:2.0

YAML_DIR = yml
MK_DIR = mk

.PHONY: *

include $(MK_DIR)/build.mk
include $(MK_DIR)/test.mk

include $(MK_DIR)/naver.mk
include $(MK_DIR)/major.mk
include $(MK_DIR)/nate.mk
include $(MK_DIR)/daum.mk
include $(MK_DIR)/bbs.mk
include $(MK_DIR)/sns.mk

include $(MK_DIR)/release.mk
include $(MK_DIR)/ps.mk

start-all: major nate naver bbs sns daum
stop-all: stop-major stop-nate stop-naver stop-bbs stop-sns stop-daum
logs-all: logs-major logs-nate logs-naver logs-bbs logs-sns logs-daum

