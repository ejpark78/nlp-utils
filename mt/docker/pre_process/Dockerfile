FROM galadriel02.korea.ncsoft.corp:5000/kmat:latest

MAINTAINER ejpark<ejaprk@ncsoft.com>
LABEL description=""

ENV DEBIAN_FRONTEND=noninteractive
ENV HOME=/root LANG=C.UTF-8 LC_ALL=C.UTF-8

# 미러 설정
ARG CACHE_SERVER=http://corpus.ncsoft.com:8081/repository/cache
ARG APT_MIRROR=http://corpus.ncsoft.com:8081/repository/ubuntu/
ARG PIP_MIRROR=http://corpus.ncsoft.com:8081/repository/pypi/simple
ARG PIP_TRUST_HOST=corpus.ncsoft.com

# 사용자 생성
ARG USER=user
ARG TOKEN=nlplab
ARG UID=1000
ARG GID=1000
ENV HOME=/home/${USER}

RUN apt clean \
    && echo && echo "# APT MIRROR 변경: ${APT_MIRROR}" \
	&& { \
		echo "deb ${APT_MIRROR} xenial main restricted universe multiverse"; \
		echo "deb ${APT_MIRROR} xenial-updates main restricted universe multiverse"; \
		echo "deb ${APT_MIRROR} xenial-backports main restricted universe multiverse"; \
	} > /etc/apt/sources.list \
    && apt update -yq \
    \
    && echo && echo "# 로케일 설치" \
    && apt install -yq --no-install-recommends --no-install-suggests \
        apt-utils \
        tzdata \
        locales \
    && echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen \
    && echo "ko_KR.UTF-8 UTF-8" >> /etc/locale.gen \
    && echo "ko_KR.EUC-KR EUC-KR" >> /etc/locale.gen \
    && locale-gen \
    \
    && echo && echo "# timezone 설정" \
    && ln -fs /usr/share/zoneinfo/Asia/Seoul /etc/localtime \
    && dpkg-reconfigure --frontend noninteractive tzdata \
    \
    && echo && echo "# 빌드 라이브러리 설치" \
    && apt install -yq --no-install-recommends --no-install-suggests \
        apt-transport-https \
        bzip2 \
        ca-certificates \
        curl \
        g++ \
        gzip \
        jq \
        libboost-all-dev \
        libbz2-dev \
        libtool \
        make \
        pkg-config \
        python-dev \
        python-pip \
        python3-dev \
        python3-pip \
        software-properties-common \
        sudo \
        tar \
        tmux \
        unzip \
        vim \
        wget \
        zlib1g-dev \
        bash \
        parallel \
    && echo && echo "# 저장소 정리" \
    && apt autoremove -y \
    && rm -rf /var/cache/* /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    \
    && echo "사용자 생성: ${USER}..." \
	&& addgroup --gid ${GID} ${USER} \
	&& useradd --uid ${UID} --gid ${GID} --home-dir ${HOME} --shell /bin/bash --comment 'container user' --create-home ${USER} \
    && usermod -aG sudo ${USER} \
	&& echo "${USER} ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

RUN echo "nltk 설치" \
	&& pip3 install --upgrade --no-cache-dir \
        nltk

RUN chown -R ${USER}:${UID} /root/server \
    && chmod -R 755 /root \
    && mv /root/server ${HOME}/

RUN python3 -c 'import nltk; nltk.download("punkt"); nltk.download("averaged_perceptron_tagger")'
