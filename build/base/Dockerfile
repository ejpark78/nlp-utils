FROM ubuntu:18.04

LABEL maintainer="ejpark@ncsoft.co.kr"

# 사용자를 root로 설정
USER root

ENV DEBIAN_FRONTEND=noninteractive
ENV HOME=/root LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV NOTVISIBLE "in users profile"

ENV APP_HOME=/usr/local/app

# 1. 설치시 사용할 경로 설정
WORKDIR $HOME

ENV APT_MIRROR=http://corpus.ncsoft.com:8081/repository/ubuntu/

RUN echo && echo "# APT MIRROR 변경: ${APT_MIRROR}" \
	&& { \
		echo "deb ${APT_MIRROR} bionic main restricted universe multiverse"; \
		echo "deb ${APT_MIRROR} bionic-updates main restricted universe multiverse"; \
		echo "deb ${APT_MIRROR} bionic-backports main restricted universe multiverse"; \
	} > /etc/apt/sources.list \
    && apt-get update -yq \
    \
    && apt-get install -yq --no-install-recommends \
        bridge-utils \
        libdb-dev \
        python3 \
        python3-dateutil \
        python3-dev \
        python3-lxml \
        python3-pip \
        curl \
    \
    && rm -rf /var/cache/* /var/lib/apt/lists/* /tmp/* /var/tmp/*

# 파이썬 라이브러리 설치
ENV PIP_TRUST_HOST=corpus.ncsoft.com
ENV PIP_MIRROR=http://${PIP_TRUST_HOST}:8081/repository/pypi/simple

RUN echo && echo "# pip 저장소 설정" \
    && mkdir -p ~/.pip \
    && { \
		echo "[global]"; \
		echo "timeout = 60"; \
		echo "index-url = ${PIP_MIRROR}"; \
		echo "trusted-host = ${PIP_TRUST_HOST}"; \
	} > ~/.pip/pip.conf \
    \
    && echo && echo "# 기본 유틸 설치" \
    && pip3 install --upgrade --no-cache-dir \
        pip \
        setuptools \
        wheel

RUN echo && echo "# 의존성 라이브러리 설치" \
    && pip3 install --upgrade --no-cache-dir \
        python-dateutil \
        boto3 \
        bs4 \
        elasticsearch \
        lxml \
        numpy \
        requests \
        requests[security] \
        selenium \
        html5lib \
        openpyxl \
        jsonlines \
        urllib3
