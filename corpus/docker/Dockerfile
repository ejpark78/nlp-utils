FROM ubuntu:20.04

LABEL maintainer="ejpark@ncsoft.co.kr"

ENV DEBIAN_FRONTEND=noninteractive
ENV HOME=/root LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV NOTVISIBLE "in users profile"

ARG APT_CODE_NAME=focal
ARG APT_MIRROR=http://mirror.kakao.com/ubuntu
ARG PIP_TRUST_HOST=mirror.kakao.com
ARG PIP_MIRROR=http://mirror.kakao.com/pypi/simple

ARG GIT_BRANCH="dev"
ARG GIT_REPO="http://ejpark:2Q9H2fF-E8sPqJXd61GC@galadriel02.korea.ncsoft.corp/crawler-dev/corpus.git"

ENV APT_OPTS="--no-install-suggests --no-install-recommends"

ENV PYTHONWARNINGS "ignore:Unverified HTTPS request"

USER root
WORKDIR $HOME

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
	&& echo && echo "# pip 저장소 설정" \
    && mkdir -p ~/.pip \
    && { \
		echo "[global]"; \
		echo "timeout = 60"; \
		echo "index-url = ${PIP_MIRROR}"; \
		echo "trusted-host = ${PIP_TRUST_HOST}"; \
	} > ~/.pip/pip.conf \
	\
	&& echo && echo "# chrome, k8s, docker 저장소 설정" \
    && apt update -yq ${APT_OPTS} \
    && apt install -yq ${APT_OPTS} \
        bash \
        curl \
        git \
        gnupg \
        libcurl4-openssl-dev \
        libssl-dev \
        locales \
        python3 \
        python3-dev \
        python3-pip \
        software-properties-common \
        tzdata \
    \
    && echo && echo "# locale 생성" \
    && locale-gen "en_US.UTF-8" \
    && locale-gen "ko_KR.UTF-8" \
    && locale-gen "ko_KR.EUC-KR" \
    && update-locale LANG=ko_KR.UTF-8 \
    && dpkg-reconfigure locales \
    \
    && echo && echo "# timezone 설정" \
    && ln -fs /usr/share/zoneinfo/Asia/Seoul /etc/localtime \
    && dpkg-reconfigure --frontend noninteractive tzdata \
    \
    && echo && echo "# python 기본 유틸 설치" \
    && pip3 install --upgrade --no-cache-dir \
        pip \
        setuptools \
        wheel \
    && pip3 install --upgrade --no-cache-dir \
        six \
        jupyterthemes \
    \
	&& echo && echo "jupyter notebook 테마 설정" \
	&& jt -t monokai -fs 11 -tfs 11 -nfs 11 -ofs 11 -cellw 980 -T -f hack -N -cellw 1280 -lineh 150 \
    \
    && apt purge -yq ${APT_OPTS} \
        gnupg \
        locales \
        software-properties-common \
        tzdata \
    && apt autoremove -yq \
    && rm -rf /var/cache/* /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN echo && echo "# datasets 설치 (git): ${GIT_REPO}" \
    && git clone -b ${GIT_BRANCH} ${GIT_REPO} /tmp/src \
    && cd /tmp/src \
    && pip3 install --upgrade --no-cache-dir -U -r requirements.txt \
    && python3 setup.py install \
    && mv /tmp/src/*.md /root/ \
    && mv /tmp/src/corpus/example /root/ \
    && rm -rf /var/cache/* /var/lib/apt/lists/* /tmp/* /var/tmp/*

ENV PORT=8888 NB_PREFIX=/ NB_TOKEN='' NB_PASSWD=''

EXPOSE ${PORT}

CMD ["bash", "-c", "jupyter notebook \
    --no-browser \
    --allow-root \
    --ip='*' \
    --port=${PORT} \
    --NotebookApp.token=${NB_TOKEN} \
    --NotebookApp.password=${NB_PASSWD} \
    --NotebookApp.terminado_settings=\"{'shell_command': ['/bin/bash']}\" \
    --ServerApp.token=${NB_TOKEN} \
    --ServerApp.password=${NB_PASSWD} \
    --ServerApp.allow_origin='*' \
    --ServerApp.base_url=${NB_PREFIX} \
    --ServerApp.iopub_data_rate_limit=10000000 \
"]
