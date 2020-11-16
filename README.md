
## private pypi 이용한 라이브러리 배포

### ~/.pip/pip.conf 설정

```bash
cat <<EOF | tee ~/.pip/pip.conf                                                        
[global]
timeout = 120

index-url=https://k8s:nlplab@nlp-utils/repository/pypi/simple
trusted-host=nlp-utils
EOF
```

### wheel 빌드 

```bash
make build
```

### 파이썬 패키지 업로드 

```bash
make upload
```

### Makefile

```makefile
build:
	python3 setup.py bdist_wheel

upload:
	CURL_CA_BUNDLE="" \
		twine upload \
			--repository-url https://nlp-utils/repository/pypi-hosted/ \
			-u k8s -p nlplab \
			--skip-existing \
			--verbose \
			dist/*
```

### 업로드 패키지 확인

https://nlp-utils/#browse/browse:pypi-hosted

### 패키지 설치

```bash
pip3 install nlplab
```
