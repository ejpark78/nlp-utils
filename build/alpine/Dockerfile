FROM alpine:3.7

LABEL maintainer="ejpark@ncsoft.com"

# koala mirror
ENV APK_MIRROR=http://172.20.79.85:88/alpine/v3.7

# koala pip_mirror
ENV PIP_MIRROR=172.20.79.85
# ENV PIP_MIRROR=mirror.kakao.com

ENV APP_HOME=/usr/local/app

# 1. 설치시 사용할 경로 설정
WORKDIR $APP_HOME

RUN echo && echo "# apk 저장소 변경" \
    && { \
		echo "${APK_MIRROR}/main"; \
		echo "${APK_MIRROR}/community"; \
	} > /etc/apk/repositories \
    \
	&& apk update \
	&& apk add --no-cache \
		bash \
        bridge-utils \
        db-dev \
        g++ \
        libffi-dev \
        libxml2 \
        libxml2-dev \
        libxslt-dev \
        openssl-dev \
        python3 \
        python3-dev \
	&& mkdir -p /usr/local/lib \
	&& apk del --purge

RUN echo && echo "# pip 저장소 설정" \
    && mkdir -p ~/.pip \
    && { \
		echo "[global]"; \
		echo "timeout = 60"; \
		echo "index-url = http://${PIP_MIRROR}:3141/root/pypi"; \
		echo "[install]"; \
		echo "trusted-host = ${PIP_MIRROR}"; \
	} > ~/.pip/pip.conf \
    \
    && echo && echo "# 기본 유틸 설치" \
    && pip3 install --upgrade --no-cache-dir --force-reinstall \
        pip \
        setuptools \
        wheel

RUN mkdir -p ${APP_HOME} 
ADD app.tar.gz ${APP_HOME}

RUN pip3 install --no-cache-dir -r /usr/local/app/requirements.txt

COPY Dockerfile ${APP_HOME}/

WORKDIR ${APP_HOME}
