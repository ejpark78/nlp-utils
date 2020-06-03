FROM ubuntu:20.04

LABEL maintainer="ejpark@ncsoft.co.kr"

# 사용자를 root로 설정
USER root

ENV DEBIAN_FRONTEND=noninteractive
ENV HOME=/root LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV NOTVISIBLE "in users profile"

ENV APP_HOME=/usr/local/app

# 1. 설치시 사용할 경로 설정
WORKDIR $HOME

ARG APT_CODE_NAME=focal
ARG APT_MIRROR=http://corpus.ncsoft.com:8081/repository/${APT_CODE_NAME}/

ARG PIP_TRUST_HOST=corpus.ncsoft.com
ARG PIP_MIRROR=http://${PIP_TRUST_HOST}:8081/repository/pypi/simple

RUN echo && echo "# APT MIRROR 변경: ${APT_MIRROR}" \
	&& { \
		echo "deb ${APT_MIRROR} ${APT_CODE_NAME} main restricted universe multiverse"; \
		echo "deb ${APT_MIRROR} ${APT_CODE_NAME}-updates main restricted universe multiverse"; \
		echo "deb ${APT_MIRROR} ${APT_CODE_NAME}-backports main restricted universe multiverse"; \
	} > /etc/apt/sources.list \
    && apt update -yq \
    && apt install -yq --no-install-recommends \
		default-jdk-headless \
        bridge-utils \
        build-essential \
        curl \
        libcurl4-openssl-dev \
        libdb-dev \
        libssl-dev \
        python3 \
        python3-dateutil \
        python3-dev \
        python3-lxml \
        python3-pip \
        software-properties-common \
        tzdata \
    && apt autoremove -yq \
    \
    && echo && echo "# timezone 설정" \
    && ln -fs /usr/share/zoneinfo/Asia/Seoul /etc/localtime \
    && dpkg-reconfigure --frontend noninteractive tzdata \
    \
    && rm -rf /var/cache/* /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN echo && echo "# install chrome" \
    && add-apt-repository -y ppa:saiarcot895/chromium-dev \
    && apt update -yq \
    && apt install -yq --no-install-recommends \
        chromium-browser \
        chromium-chromedriver \
    && rm -rf /var/cache/* /var/lib/apt/lists/* /tmp/* /var/tmp/*

# 파이썬 라이브러리 설치
RUN echo && echo "# pip 저장소 설정" \
    && mkdir -p ~/.pip \
    && { \
		echo "[global]"; \
		echo "timeout = 60"; \
		echo "index-url = ${PIP_MIRROR}"; \
		echo "trusted-host = ${PIP_TRUST_HOST}"; \
	} > ~/.pip/pip.conf \
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
        requests[socks] \
        requests[security] \
        selenium \
        html5lib \
        openpyxl \
        jsonlines \
        urllib3 \
        pandas \
        pycurl \
        cachelib
