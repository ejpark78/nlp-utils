FROM debian:stretch-slim

LABEL maintainer="ejpark@ncsoft.co.kr"


# 사용자를 root로 설정
USER root

ENV DEBIAN_FRONTEND=noninteractive
ENV HOME=/root LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV NOTVISIBLE "in users profile"

# frodo
ENV APT_MIRROR=mirror.kakao.com
#ENV APT_MIRROR=nlp.ncsoft.com:8010
ENV APP_HOME=/usr/local/app

ENV PIP_MIRROR=mirror.kakao.com
#ENV PIP_MIRROR=nlp.ncsoft.com

# 1. 설치시 사용할 경로 설정
WORKDIR $HOME

RUN echo && echo "# apt 저장소 변경" \
    && rm -rf /var/lib/apt/lists/* \
	&& { \
		echo "deb http://${APT_MIRROR}/debian stretch main contrib non-free"; \
#        echo "deb http://${APT_MIRROR}/debian-security stretch/updates main contrib"; \
	} > /etc/apt/sources.list \
    && apt-get update -yq \
    \
    && apt-get install -yq --no-install-recommends \
        bridge-utils \
        build-essential \
        libdb-dev \
        python3 \
        python3-dateutil \
        python3-dev \
        python3-lxml \
        python3-pip \
    \
    && rm -rf /var/cache/* /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN echo && echo "# pip 저장소 설정" \
    && mkdir -p ~/.pip \
    && { \
		echo "[global]"; \
		echo "timeout = 60"; \
#		echo "index-url = http://${PIP_MIRROR}:3141/root/pypi"; \
		echo "index-url = http://${PIP_MIRROR}/pypi/simple"; \
		echo "[install]"; \
		echo "trusted-host = ${PIP_MIRROR}"; \
	} > ~/.pip/pip.conf \
    \
    && echo && echo "# 기본 유틸 설치" \
    && pip3 install --upgrade --no-cache-dir \
        pip \
        setuptools \
        wheel

RUN mkdir -p ${APP_HOME} 
ADD app.tar.gz ${APP_HOME}

RUN pip3 install --no-cache-dir -r /usr/local/app/requirements.txt

COPY Dockerfile ${APP_HOME}

WORKDIR ${APP_HOME}
#CMD ["python3", "app.py"]
