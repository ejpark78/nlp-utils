ARG BASE_IMAGE=tensorflow/tensorflow:2.3.0

FROM ${BASE_IMAGE}

LABEL author="박은진<ejpark78@gmail.com>"

ENV DEBIAN_FRONTEND=noninteractive
ENV HOME=/root LANG=C.UTF-8 LC_ALL=C.UTF-8 LANGUAGE=ko_KR:en

ARG APT_CODE_NAME=bionic
ARG APT_MIRROR=http://mirror.kakao.com/ubuntu
ARG PIP_MIRROR=http://mirror.kakao.com/pypi/simple
ARG PIP_TRUST_HOST=mirror.kakao.com

ENV APT_OPTS="--no-install-suggests --no-install-recommends"

RUN echo && echo "# APT MIRROR 변경: ${APT_MIRROR}" \
	&& { \
		echo "deb ${APT_MIRROR} ${APT_CODE_NAME} main restricted universe multiverse"; \
		echo "deb ${APT_MIRROR} ${APT_CODE_NAME}-updates main restricted universe multiverse"; \
		echo "deb ${APT_MIRROR} ${APT_CODE_NAME}-backports main restricted universe multiverse"; \
	} > /etc/apt/sources.list \
    \
	&& { \
		echo "Acquire::https {"; \
		echo "  Verify-Peer false;"; \
		echo "  Verify-Host false;"; \
		echo "};"; \
	} > /etc/apt/apt.conf.d/mirror.conf \
    \
    && apt update -yq ${APT_OPTS} \
    && apt install -yq ${APT_OPTS} \
        cmake \
        build-essential \
        git-core \
    && echo && echo "# 저장소 정리" \
    && rm -rf /var/cache/* /var/lib/apt/lists/* /tmp/* /var/tmp/*

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
    && pip3 install --upgrade --no-cache-dir --force-reinstall \
        pip \
        setuptools \
        wheel \
		cython \
	&& rm -rf /tmp/*

ENV BUILD_HOME=/usr/local

RUN echo && echo "# facebookresearch/fastText 설치" \
    && cd ${BUILD_HOME} \
    && git config --global http.sslVerify false \
    && git clone --depth 1 https://github.com/facebookresearch/fastText.git fastText \
    \
    && mkdir fastText/build \
    && cd fastText/build \
    && cmake -DCMAKE_INSTALL_PREFIX=/app/fastText .. \
    && make -j $(nproc) \
    && make install \
    \
    && cd .. \
    && pip3 install . \
	&& rm -rf /tmp/*
