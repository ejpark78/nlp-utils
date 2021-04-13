ARG BUILD_IMAGE=corpus:5000/mtops/moses:build
FROM $BUILD_IMAGE AS build

FROM ubuntu:18.04

MAINTAINER ejpark<ejaprk@ncsoft.com>
LABEL description="Base on https://github.com/moses-smt/mosesdecoder/blob/RELEASE-4.0/scripts/docker/Dockerfile.ubuntu.fastlightpbmt"

ENV DEBIAN_FRONTEND=noninteractive
ENV HOME=/root LANG=C.UTF-8 LC_ALL=C.UTF-8

ENV APP_HOME=/usr/local

ENV MOSES=${APP_HOME}/mosesdecoder
ENV MOSES_SCRIPTS=${MOSES}/scripts/training

ENV PATH=${PATH}:${MOSES}/bin:${MOSES_SCRIPTS}:.

# 미러 설정
ARG CACHE_SERVER=http://corpus.ncsoft.com:8081/repository/cache
ARG APT_MIRROR=http://corpus.ncsoft.com:8081/repository/ubuntu/
ARG PIP_MIRROR=http://corpus.ncsoft.com:8081/repository/pypi/simple
ARG PIP_TRUST_HOST=corpus.ncsoft.com

# 사용자 생성
ARG UID=1000
ARG GID=1000
ARG USER=user
ARG TOKEN=nlplab
ENV HOME=/home/${USER}
ENV PERL_MM_USE_DEFAULT=1
ENV CURL_CA_BUNDLE=""

ENV TERM xterm
ENV ZSH_THEME agnoster

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
        autoconf \
        bzip2 \
        ca-certificates \
        curl \
        dtrx \
        g++ \
        gzip \
        jq \
        libboost-all-dev \
        libbz2-dev \
        liblzma-dev \
        libicu-dev \
        libtool \
        libxmlrpc-c++8-dev \
        libxmlrpc-core-c3-dev \
        libgoogle-perftools-dev \
        make \
        perl \
        pkg-config \
        python-dev \
        python-pip \
        python3-dev \
        python3-pip \
        python3-setuptools \
        software-properties-common \
        sudo \
        tar \
        tmux \
        unzip \
        vim \
        wget \
        zlib1g-dev \
        bash \
        zsh \
        parallel \
    && echo && echo "# 저장소 정리" \
    && apt autoremove -y \
    && rm -rf /var/cache/* /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    \
    && echo && echo "oh my zsh 설치" \
    && curl -L https://github.com/robbyrussell/oh-my-zsh/raw/master/tools/install.sh | zsh || true \
    \
    && echo && echo "사용자 생성: ${USER}..." \
	&& addgroup --gid ${GID} ${USER} \
	&& useradd --uid ${UID} --gid ${GID} --home-dir ${HOME} --shell /bin/zsh --comment 'container user' --create-home ${USER} \
    && usermod -aG sudo ${USER} \
	&& echo "${USER} ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers \
    \
    && echo && echo "perl lib 설치" \
    && cpan install XML::Twig \
    && cpan install Sort::Naturally \
    && cpan install String::Util

COPY --from=build /usr/local/mosesdecoder /usr/local/mosesdecoder

RUN chown -R ${USER} /usr/local/mosesdecoder

WORKDIR ${HOME}

ADD bin.tar ${HOME}/bin

RUN chown -R ${USER} ${HOME} \
    && pip3 install -r ${HOME}/bin/requirements.txt

USER ${USER}
