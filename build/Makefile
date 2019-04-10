
CONTAINER = crawler

# image
BASE_IMAGE = corpus:5000/base/crawler:latest

IMAGE = corpus:5000/crawler
IMAGE_TAG = $(shell date +%F.%H)

# Mirror
APT_MIRROR = http://corpus.ncsoft.com:8081/repository/ubuntu/
PIP_MIRROR = http://corpus.ncsoft.com:8081/repository/pypi/simple
PIP_TRUST_HOST = corpus.ncsoft.com

# path
YAML_DIR = yml
MK_DIR = mk

CRAWLER_OPT =
MQ_HOSTS = mq-server:172.20.78.254

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

# batch
all-start: major-start nate-start naver-start daum-start bbs-start sns-start
all-stop: major-stop nate-stop naver-stop daum-stop bbs-stop sns-stop
all-logs: major-logs nate-logs naver-logs daum-logs bbs-logs sns-logs
