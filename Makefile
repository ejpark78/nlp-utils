
GIT_TAG = $(shell git describe --tags --long | cut -f1,2 -d'-' | tr '-' '.')
GIT_COMMIT = $(shell git rev-list --count HEAD)

.PHONY: *

.ONESHELL:
reinstall: clean build uninstall install

.ONESHELL:
install:
	echo $(GIT_TAG).$(GIT_COMMIT) > version
	python3 setup.py install

.ONESHELL:
wheel:
	echo $(GIT_TAG).$(GIT_COMMIT) > version
	python3 setup.py bdist_wheel

.ONESHELL:
wheel-install:
	pip3 install dist/*.whl

.ONESHELL:
upload:
	CURL_CA_BUNDLE="" \
		twine upload \
			--repository-url https://nlp-utils/repository/pypi-hosted/ \
			-u k8s -p nlplab \
			--skip-existing \
			--verbose \
			dist/*

.ONESHELL:
uninstall:
	pip3 uninstall -y crawler

.ONESHELL:
clean:
	rm -rf build dist crawler.egg-info

# pip3 install git+http://galadriel02.korea.ncsoft.corp/searchtf/pypi/nlplab.git
