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
        automake \
        build-essential \
        curl \
        g++ \
        git-core \
        openjdk-8-jdk \
        python3-dev \
        python3-pip \
        wget \
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

RUN echo && echo "# mecab_ko 설치" \
    && cd ${BUILD_HOME} \
    && curl -LO https://bitbucket.org/eunjeon/mecab-ko/downloads/mecab-0.996-ko-0.9.2.tar.gz \
    && tar zxfv mecab-0.996-ko-0.9.2.tar.gz \
    && rm mecab-0.996-ko-0.9.2.tar.gz \
    && mv mecab-0.996-ko-0.9.2 mecab \
    && cd mecab \
    && ./configure \
    && make -j $(nproc) \
    && make check \
    && make install \
	&& rm -rf /tmp/* \
    \
    && cd ${BUILD_HOME} \
    && tar cvfz mecab.tar.gz mecab

RUN echo && echo "# mecab-ko-dic 설치" \
    && cd ${BUILD_HOME} \
    && curl -LO https://bitbucket.org/eunjeon/mecab-ko-dic/downloads/mecab-ko-dic-2.1.1-20180720.tar.gz \
    && tar zxvf mecab-ko-dic-2.1.1-20180720.tar.gz \
    && rm mecab-ko-dic-2.1.1-20180720.tar.gz \
    && mv mecab-ko-dic-2.1.1-20180720 mecab-ko-dic \
    && cd mecab-ko-dic \
    && ./autogen.sh \
    && ./configure \
    && mecab-config --libs-only-L | tee /etc/ld.so.conf.d/mecab.conf \
    && ldconfig -v \
    && make -j $(nproc) \
    && echo "dicdir=/usr/local/lib/mecab/dic/mecab-ko-dic" > /usr/local/etc/mecabrc \
    && make install \
	&& rm -rf /tmp/* \
    \
    && cd ${BUILD_HOME} \
    && tar cvfz mecab-ko-dic.tar.gz mecab-ko-dic

RUN echo && echo "# mecab-python 설치" \
    && cd ${BUILD_HOME} \
    && git clone https://bitbucket.org/eunjeon/mecab-python-0.996.git mecab-python \
    && cd mecab-python \
    && pip3 install -U pip \
    && pip3 install mecab-python \
	&& rm -rf /tmp/* \
    \
    && cd ${BUILD_HOME} \
    && tar cvfz mecab-python.tar.gz mecab-python

RUN echo && echo "# konlpy 설치" \
    && cd ${BUILD_HOME} \
    \
    && pip3 install -U pip \
    && pip3 install -U konlpy \
    \
    && git clone https://github.com/konlpy/konlpy konlpy \
    && cd konlpy \
    && pip3 install -r requirements-dev.txt \
	&& rm -rf /tmp/* \
    \
    && cd ${BUILD_HOME} \
    && tar cvfz konlpy.tar.gz konlpy

ARG MINIO_URI=http://172.19.168.48:9000
ARG MINIO_ACCESS_KEY="minio"
ARG MINIO_SECRET_KEY="minio123"
ARG MINIO_BUCKET="cache"
ARG MINIO_PATH="build"

RUN echo && echo "minio client" \
	&& wget https://dl.min.io/client/mc/release/linux-amd64/mc \
	&& chmod +x mc \
	&& mv mc /usr/bin/ \
	\
	&& mc alias set ${MINIO_BUCKET} ${MINIO_URI} ${MINIO_ACCESS_KEY} ${MINIO_SECRET_KEY} \
	&& mc cp ${BUILD_HOME}/mecab.tar.gz ${MINIO_BUCKET}/${MINIO_PATH}/mecab.tar.gz \
	&& mc cp ${BUILD_HOME}/mecab-ko-dic.tar.gz ${MINIO_BUCKET}/${MINIO_PATH}/mecab-ko-dic.tar.gz \
	&& mc cp ${BUILD_HOME}/mecab-python.tar.gz ${MINIO_BUCKET}/${MINIO_PATH}/mecab-python.tar.gz \
	&& mc cp ${BUILD_HOME}/konlpy.tar.gz ${MINIO_BUCKET}/${MINIO_PATH}/konlpy.tar.gz

CMD ["python3 -m pytest -v ."]
