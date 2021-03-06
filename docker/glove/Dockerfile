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
        build-essential \
        git-core \
        unzip \
        wget \
    && echo && echo "# 저장소 정리" \
    && rm -rf /var/cache/* /var/lib/apt/lists/* /tmp/* /var/tmp/*

ENV BUILD_HOME=/usr/local

RUN echo && echo "# stanfordnlp/glove 설치" \
    && cd ${BUILD_HOME} \
    && git config --global http.sslVerify false \
    && git clone --depth 1 https://github.com/stanfordnlp/glove glove \
    && cd glove \
    && make -j $(nproc) \
	&& rm -rf /tmp/* \
    \
    && cd ${BUILD_HOME} \
    && tar cvfz glove.tar.gz glove

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
	&& mc cp ${BUILD_HOME}/glove.tar.gz ${MINIO_BUCKET}/${MINIO_PATH}/glove.tar.gz
