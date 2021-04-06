
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
upload: wheel
	curl -s -k -u k8s:nlplab -X DELETE \
		"https://nlp-utils/service/rest/v1/components/$(shell curl -s -k -u k8s:nlplab -X GET 'https://nlp-utils/service/rest/v1/search?repository=pypi-hosted&name=crawler' | jq -r '.items[].id')"

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

.ONESHELL:
airflow-env:
	export AIRFLOW_HOME=$(shell pwd)/airflow
	export AIRFLOW__CORE__LOAD_EXAMPLES=False
	export AIRFLOW__KUBERNETES__GIT_DAGS_FOLDER_MOUNT_POINT=$(shell pwd)
	export AIRFLOW__KUBERNETES__GIT_DAGS_VOLUME_SUBPATH=dags
	export AIRFLOW_DAGS_FOLDER=$(shell pwd)/dags

.ONESHELL:
push-subtree:
	git subtree push --prefix config config dev
	git subtree push --prefix dags dags dev
	git subtree push --prefix docker docker dev
	git subtree push --prefix helm helm dev
	git subtree push --prefix http http dev

.ONESHELL:
docker-states:
	watch -n 30 -d 'docker stats --no-stream --all --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"'


# pip3 install git+http://galadriel02.korea.ncsoft.corp/searchtf/pypi/nlplab.git
