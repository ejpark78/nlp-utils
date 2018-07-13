FROM debian:stretch

LABEL maintainer="ejpark@ncsoft.co.kr"


# 사용자를 root로 설정
USER root

ENV DEBIAN_FRONTEND=noninteractive
ENV HOME=/root LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV NOTVISIBLE "in users profile"

# frodo
ENV APT_MIRROR=172.20.51.91
ENV APP_HOME=/usr/local/app


# 1. 설치시 사용할 경로 설정
WORKDIR $HOME


# 2. apt 저장소 변경 / 로케일 및 유틸 설치 / sshd 설정 변경: X11 forwarding 설정
        # echo "deb http://${APT_MIRROR}/debian stretch-updates main contrib non-free"; \
        # echo "deb http://${APT_MIRROR}/debian stretch-backports main contrib non-free"; \
RUN echo && echo "# apt 저장소 변경" \
    && rm -rf /var/lib/apt/lists/* \
	&& { \
		echo "deb http://${APT_MIRROR}/debian stretch main contrib non-free"; \
        echo "deb http://${APT_MIRROR}/debian-security stretch/updates main contrib"; \
	} > /etc/apt/sources.list \
    && apt-get update -yq \
    \
    && echo && echo "# 로케일 설치" \
    && apt-get install -yq --no-install-recommends --no-install-suggests \
        locales \
    && echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen \
    && echo "ko_KR.UTF-8 UTF-8" >> /etc/locale.gen \
    && echo "ko_KR.EUC-KR EUC-KR" >> /etc/locale.gen \
    && locale-gen \
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
		echo "index-url = http://${APT_MIRROR}:3141/root/pypi"; \
		echo "[install]"; \
		echo "trusted-host = ${APT_MIRROR}"; \
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
