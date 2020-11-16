

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

clean:
	rm -rf build dist *.egg-info
