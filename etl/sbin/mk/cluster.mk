
HOME_DIR = ../../..
SBIN_DIR = $(HOME_DIR)/sbin/text_pool

.ONESHELL:
ps-cluster:
	time parallel -j 10 -k --bar -a $(SBIN_DIR)/all.list \
		$(SBIN_DIR)/ps.sh {}

.ONESHELL:
images-cluster:
	time parallel -j 10 -k --bar -a $(SBIN_DIR)/all.list \
		$(SBIN_DIR)/images.sh {}
