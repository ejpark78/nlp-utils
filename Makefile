
reinstall: clean build uninstall install

build:
	python3 setup.py bdist_wheel

install:
	pip3 install dist/nlplab-1.*.whl

upload:
	CURL_CA_BUNDLE="" \
		twine upload \
			--repository-url https://nlp-utils/repository/pypi-hosted/ \
			-u k8s -p nlplab \
			--skip-existing \
			--verbose \
			dist/*

uninstall:
	pip3 uninstall -y nlplab

clean:
	rm -rf build dist src/*.egg-info
