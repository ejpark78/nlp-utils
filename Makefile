
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
add-remote:
	git remote add config http://galadriel02.korea.ncsoft.corp/crawler-dev/config.git
	git remote add helm http://galadriel02.korea.ncsoft.corp/crawler-dev/helm.git
	git remote add dags http://galadriel02.korea.ncsoft.corp/crawler-dev/dags.git
	git remote add http http://galadriel02.korea.ncsoft.corp/crawler-dev/http.git
	git remote add docker http://galadriel02.korea.ncsoft.corp/crawler-dev/docker.git
	git remote add corpus http://galadriel02.korea.ncsoft.corp/crawler-dev/corpus.git

.ONESHELL:
add-subtree:
	git subtree add --prefix config config dev
	git subtree add --prefix helm helm dev
	git subtree add --prefix dags dags dev
	git subtree add --prefix http http dev
	git subtree add --prefix docker docker dev
	git subtree add --prefix corpus corpus dev

.ONESHELL:
push-subtree:
	git subtree push --prefix config config dev
	git subtree push --prefix dags dags dev
	git subtree push --prefix docker docker dev
	git subtree push --prefix helm helm dev
	git subtree push --prefix http http dev
	git subtree push --prefix corpus corpus dev

.ONESHELL:
docker-states:
	watch -n 30 -d 'docker stats --no-stream --all --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"'


# pip3 install git+http://galadriel02.korea.ncsoft.corp/searchtf/pypi/nlplab.git

