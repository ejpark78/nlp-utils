
# path
MK_DIR = mk
YAML_DIR = yml

.PHONY: *

include $(MK_DIR)/env.mk
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
