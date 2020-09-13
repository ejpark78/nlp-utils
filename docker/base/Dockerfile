ARG GLOVE=registry/utils/glove:latest
ARG MECAB=registry/utils/mecab:latest
ARG KHAIII=registry/utils/khaiii:latest
ARG FAST_TEXT=registry/utils/fast_text:latest
ARG REQUIREMENTS=registry/dev/utils/requirements:latest
ARG SENTENCE_PIECE=registry/utils/sentencepiece:latest
ARG BASE_IMAGE=tensorflow/tensorflow:2.3.0

FROM ${GLOVE} AS glove
FROM ${MECAB} AS mecab
FROM ${KHAIII} AS khaiii
FROM ${FAST_TEXT} AS fast_text
FROM ${REQUIREMENTS} AS requirements
FROM ${SENTENCE_PIECE} AS sentencepiece

FROM ${BASE_IMAGE}

LABEL author="박은진<ejpark78@gmail.com>"

ENV DEBIAN_FRONTEND=noninteractive
ENV HOME=/root LANG=C.UTF-8 LC_ALL=C.UTF-8 LANGUAGE=ko_KR:en

ARG APT_CODE_NAME=bionic
ARG APT_MIRROR=http://mirror.kakao.com/ubuntu
ARG PIP_MIRROR=http://mirror.kakao.com/pypi/simple
ARG PIP_TRUST_HOST=mirror.kakao.com

ENV APT_OPTS="--no-install-suggests --no-install-recommends"

USER root

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
        apt-transport-https \
        build-essential \
        bzip2 \
        ca-certificates \
        cmake \
        curl \
        dos2unix \
        fontconfig \
        git \
        gzip \
        htop \
        jq \
        language-pack-ko \
        libcurl4-openssl-dev \
        libgoogle-perftools-dev \
        libssl-dev \
        libxml2-dev \
        libxslt-dev \
        locales \
        net-tools \
        openjdk-8-jdk \
        p7zip \
        parallel \
        pbzip2 \
        pkg-config \
        python3 \
        python3-dev \
        python3-pip \
        python3-pycurl \
        sqlite3 \
        sudo \
        texlive-base \
        tmux \
        tzdata \
        unzip \
        vim \
        wget \
        zip \
        zsh \
    && echo && echo "# 폰트 초기화 & 한글 폰트 설치" \
    && apt install -yq ${APT_OPTS} \
        fonts-baekmuk \
        fonts-nanum* \
        fonts-unfonts-core \
        fonts-unfonts-extra \
    && rm -rf /usr/share/fonts/truetype/dejavu \
    && fc-cache -f -v \
    && fmtutil-sys --all \
    \
    && echo && echo "# 저장소 정리" \
    && rm -rf /var/cache/* /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN echo && echo "nodejs 설치" \
    && curl -sL https://deb.nodesource.com/setup_12.x | sudo -E bash - \
    && apt update -yq ${APT_OPTS} \
    && apt install -yq ${APT_OPTS} \
        nodejs \
    && echo && echo "# 저장소 정리" \
    && rm -rf /var/cache/* /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN echo && echo "# locale-gen" \
    && { \
		echo "en_US.UTF-8 UTF-8"; \
		echo "ko_KR.UTF-8 UTF-8"; \
		echo "ko_KR.EUC-KR EUC-KR"; \
	} >> /etc/locale.gen \
    && locale-gen \
    && locale-gen ko_KR.UTF-8 \
    && update-locale LANG=ko_KR.UTF-8 \
    && dpkg-reconfigure locales \
    \
    && echo && echo "# timezone 설정" \
    && ln -fs /usr/share/zoneinfo/Asia/Seoul /etc/localtime \
    && dpkg-reconfigure --frontend noninteractive tzdata \
    \
    && wget https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.1.1-linux-x86_64.tar.bz2 \
    && tar xvjf phantomjs-2.1.1-linux-x86_64.tar.bz2 \
    && mv phantomjs-2.1.1-linux-x86_64 /usr/local/share \
    && rm phantomjs-2.1.1-linux-x86_64.tar.bz2 \
    && ln -sf /usr/local/share/phantomjs-2.1.1-linux-x86_64/bin/phantomjs /usr/local/bin

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
		cython \
        cmake \
        pip \
        pytest-runner \
        setuptools \
        wheel \
    && rm -rf /tmp/*

ENV BUILD_HOME=/usr/local

# requirements 설치
# COPY --from=requirements /usr/local/bin /usr/local/bin
# COPY --from=requirements /usr/local/lib /usr/local/lib
# COPY --from=requirements /usr/local/share/jupyter /usr/local/share/jupyter
# COPY --from=requirements /usr/local/share/jupyterhub /usr/local/share/jupyterhub

# sentencepiece 설치
COPY --from=sentencepiece ${BUILD_HOME}/sentencepiece ${BUILD_HOME}/sentencepiece

RUN echo && echo "# sentencepiece 설치" \
    && cd ${BUILD_HOME}/sentencepiece/build \
    && make install \
    && ldconfig -v \
    && rm -rf ${BUILD_HOME}/sentencepiece /tmp/*

# konlpy/mecab 설치
COPY --from=mecab ${BUILD_HOME}/mecab ${BUILD_HOME}/mecab
COPY --from=mecab ${BUILD_HOME}/mecab-ko-dic ${BUILD_HOME}/mecab-ko-dic
COPY --from=mecab ${BUILD_HOME}/mecab-python ${BUILD_HOME}/mecab-python

RUN echo && echo "# konlpy/mecab 설치" \
    && cd ${BUILD_HOME}/mecab \
    && make check \
    && make install \
    && rm -rf ${BUILD_HOME}/mecab \
    \
    && cd ${BUILD_HOME}/mecab-ko-dic \
    && mecab-config --libs-only-L | $sudo tee /etc/ld.so.conf.d/mecab.conf \
    && ldconfig -v \
    && make -j $(nproc) \
    && echo "dicdir=/usr/local/lib/mecab/dic/mecab-ko-dic" > /usr/local/etc/mecabrc \
    && make install \
    && rm -rf ${BUILD_HOME}/mecab-ko-dic \
    \
    && cd ${BUILD_HOME}/mecab-python \
    && pip3 install mecab-python \
    && rm -rf ${BUILD_HOME}/mecab-python /tmp/*

# stanfordnlp/glove 설치
COPY --from=glove ${BUILD_HOME}/glove ${BUILD_HOME}/glove

# facebookresearch/fastText 설치
COPY --from=fast_text ${BUILD_HOME}/fastText ${BUILD_HOME}/fastText

RUN echo && echo "# facebookresearch/fastText 설치" \
    && cd ${BUILD_HOME}/fastText/build \
    && make install \
    && cd .. \
    && pip3 install --upgrade --no-cache-dir . \
    && rm -rf ${BUILD_HOME}/fastText /tmp/*

# kakao/khaiii 설치
COPY --from=khaiii ${BUILD_HOME}/khaiii ${BUILD_HOME}/khaiii
COPY --from=khaiii /root/.hunter ${HOME}/.hunter

RUN echo && echo "# kakao/khaiii 설치" \
    && cd ${BUILD_HOME}/khaiii/build \
    && make resource \
    && make large_resource \
    && make install \
    \
    && cd package_python \
    && pip3 install . \
    \
    && rm -rf ${BUILD_HOME}/khaiii ${HOME}/.hunter /tmp/*

ARG USER=user
ARG UID=1000
ARG GID=1000

ENV USER=${USER} HOME=/home/${USER}

RUN echo "# 사용자 생성: ${USER}..." \
	&& addgroup --gid ${GID} ${USER} \
	&& useradd --uid ${UID} --gid ${GID} -d ${HOME} -s /bin/zsh -m ${USER} \
    && usermod -d ${HOME} ${USER} \
    && chown -R ${UID}:${GID} ${HOME} \
	&& usermod -G sudo ${USER} \
	&& echo "${USER} ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

WORKDIR ${HOME}
USER ${USER}

ARG docker_image
ARG docker_tag
ARG build_date
ARG git_url
ARG git_branch
ARG git_tag
ARG git_commit_id
ARG git_commit_count

ENV docker_image=${docker_image}
ENV docker_tag=${docker_tag}
ENV build_date=${build_date}
ENV git_url=${git_url}
ENV git_branch=${git_branch}
ENV git_tag=${git_tag}
ENV git_commit_id=${git_commit_id}
ENV git_commit_count=${git_commit_count}
