ARG BASE_IMAGE=nvidia/cuda:10.2-cudnn7-devel-ubuntu18.04
FROM ${BASE_IMAGE}

MAINTAINER ejpark<ejaprk@ncsoft.com>
LABEL description="Base on https://github.com/OpenNMT/OpenNMT-py"

ENV DEBIAN_FRONTEND=noninteractive
ENV HOME=/root LANG=C.UTF-8 LC_ALL=C.UTF-8

ENV APP_HOME=/usr/local

# 미러 설정
ARG CACHE_SERVER=http://corpus.ncsoft.com:8081/repository/cache
ARG APT_MIRROR=http://corpus.ncsoft.com:8081/repository/bionic/
ARG PIP_MIRROR=http://corpus.ncsoft.com:8081/repository/pypi/simple
ARG PIP_TRUST_HOST=corpus.ncsoft.com

# 사용자 생성
ARG USER=user
ARG TOKEN=nlplab
ARG UID=1000
ARG GID=1000
ENV HOME=/home/${USER}
ENV PERL_MM_USE_DEFAULT=1
ENV CURL_CA_BUNDLE=""

RUN apt clean \
    && echo && echo "# APT MIRROR 변경: ${APT_MIRROR}" \
	&& { \
		echo "deb ${APT_MIRROR} bionic main restricted universe multiverse"; \
		echo "deb ${APT_MIRROR} bionic-updates main restricted universe multiverse"; \
		echo "deb ${APT_MIRROR} bionic-backports main restricted universe multiverse"; \
	} > /etc/apt/sources.list \
    && apt update -yq \
    \
    && echo && echo "# 로케일 설치" \
    && apt install -yq --no-install-recommends --no-install-suggests \
        apt-utils \
        tzdata \
        locales \
    && { \
		echo "en_US.UTF-8 UTF-8"; \
		echo "ko_KR.UTF-8 UTF-8"; \
		echo "ko_KR.EUC-KR EUC-KR"; \
	} >> /etc/locale.gen \
    && locale-gen \
    \
    && echo && echo "# timezone 설정" \
    && ln -fs /usr/share/zoneinfo/Asia/Seoul /etc/localtime \
    && dpkg-reconfigure --frontend noninteractive tzdata \
    \
    && echo && echo "# 빌드 라이브러리 설치" \
    && apt install -yq --no-install-recommends --no-install-suggests \
        apt-transport-https \
        build-essential \
        bzip2 \
        ca-certificates \
        curl \
        git \
        gzip \
        jq \
        libczmq-dev \
        libffi-dev \
        libtool \
        libzmq3-dev \
        p7zip \
        parallel \
        pbzip2 \
        python3 \
        python3-pip \
        python3-setuptools \
        python3-dev \
        python3-venv \
        rename \
        software-properties-common \
        sqlite3 \
        sudo \
        tmux \
        unzip \
        vim \
        wget \
        zip \
        zsh \
    \
    && echo && echo "# 저장소 정리" \
    && apt autoremove -y \
    && rm -rf /var/cache/* /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN echo "open nmt 설치" \
	&& pip3 install --upgrade --no-cache-dir \
		keras \
        torchvision \
		tensorflow-gpu \
	&& pip3 install --upgrade --no-cache-dir \
        OpenNMT-py \
    && cpan install XML:Twig \
    && cpan install Sort:Naturally \
    && cpan install String:Util

RUN echo "사용자 생성: ${USER}..." \
	&& addgroup --gid ${GID} ${USER} \
	&& useradd --uid ${UID} --gid ${GID} -d ${HOME} -s /bin/zsh -m ${USER} \
    && usermod -d ${HOME} ${USER} \
    && echo && echo "# sudo 그룹 할당: ${USER}" \
	&& usermod -G sudo ${USER} \
	&& echo "${USER} ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

WORKDIR ${HOME}

ADD bin.tar ${HOME}/bin

RUN chown -R ${USER} ${HOME} \
    && pip3 install -r ${HOME}/bin/requirements.txt

USER ${USER}

# cuda 버전 확인
# cat /usr/local/cuda/version.txt
# cat /usr/include/cudnn.h | grep -E "CUDNN_MAJOR|CUDNN_MINOR|CUDNN_PATCHLEVEL"

