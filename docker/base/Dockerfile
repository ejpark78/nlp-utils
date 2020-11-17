FROM ubuntu:20.04

LABEL maintainer="ejpark@ncsoft.co.kr"

ENV DEBIAN_FRONTEND=noninteractive
ENV HOME=/root LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV NOTVISIBLE "in users profile"

ARG APT_CODE_NAME=focal
ARG APT_MIRROR=http://mirror.kakao.com/ubuntu
ARG PIP_TRUST_HOST=mirror.kakao.com
ARG PIP_MIRROR=http://mirror.kakao.com/pypi/simple

ENV APT_OPTS="--no-install-suggests --no-install-recommends"

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
    && apt update -yq ${APT_OPTS} \
    && apt install -yq ${APT_OPTS} \
		bash \
		default-jdk-headless \
        bridge-utils \
        build-essential \
        ca-certificates \
        curl \
        git \
        gpg-agent \
        jq \
        libcurl4-openssl-dev \
        libdb-dev \
        libssl-dev \
        parallel \
        python3 \
        python3-dateutil \
        python3-dev \
        python3-lxml \
        python3-pip \
        software-properties-common \
        tmux \
        tzdata \
        wget \
        zsh \
    && echo && echo "# timezone 설정" \
    && ln -fs /usr/share/zoneinfo/Asia/Seoul /etc/localtime \
    && dpkg-reconfigure --frontend noninteractive tzdata \
    && echo && echo "# oh my zsh 설치" \
    && wget https://github.com/robbyrussell/oh-my-zsh/raw/master/tools/install.sh -O - | zsh || true \
    && apt autoremove -yq \
    && rm -rf /var/cache/* /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN echo && echo "nodejs 설치" \
    && curl -sL https://deb.nodesource.com/setup_12.x | bash - \
    && apt update -yq ${APT_OPTS} \
    && apt install -yq ${APT_OPTS} \
        nodejs \
    && echo && echo "# 저장소 정리" \
    && rm -rf /var/cache/* /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN echo && echo "minio client" \
	&& wget https://dl.min.io/client/mc/release/linux-amd64/mc \
	&& chmod +x mc \
	&& mv mc /usr/bin/

# 파이썬 라이브러리 설치
RUN echo && echo "# pip 저장소 설정" \
    && mkdir -p ~/.pip \
    && { \
		echo "[global]"; \
		echo "timeout = 60"; \
		echo "index-url = ${PIP_MIRROR}"; \
		echo "trusted-host = ${PIP_TRUST_HOST}"; \
	} > ~/.pip/pip.conf \
    && echo && echo "# 기본 유틸 설치" \
    && pip3 install --upgrade --no-cache-dir \
        pip \
        setuptools \
        wheel \
    && echo && echo "# 의존성 라이브러리 설치" \
    && pip3 install --upgrade --no-cache-dir \
        apache-airflow \
        bs4 \
        cachelib \
        elasticsearch \
        html5lib \
        jsonlines \
        lxml \
        openpyxl \
        pycurl \
        python-dateutil \
        qgrid \
        requests \
        requests[security] \
        requests[socks] \
        selenium \
        urllib3 \
    && rm -rf /tmp/*

RUN echo && echo "# jupyter 설치" \
    && pip3 install --upgrade --no-cache-dir \
        jupyter \
        jupyterlab \
        jupyterthemes \
		autopep8 \
		bash_kernel \
        sshkernel \
    && echo && echo "jupyter kernel 설치" \
    && python3 -m sshkernel install \
    && python3 -m bash_kernel.install \
	\
    && echo && echo "nbextension enable 설정" \
    && jupyter labextension install qgrid \
	&& jupyter labextension install ipyvolume \
    && jupyter labextension install @jupyter-widgets/jupyterlab-manager \
	\
	&& echo && echo "nbextension enable 설정" \
	&& jupyter nbextension enable --py --sys-prefix qgrid \
    && jupyter nbextension enable --py --sys-prefix widgetsnbextension \
	\
    && jupyter serverextension enable --py jupyterlab --sys-prefix \
	\
	&& echo && echo "jupyter notebook 테마 설정" \
	&& jt -t monokai -fs 11 -tfs 11 -nfs 11 -ofs 11 -cellw 980 -T -f hack -N -cellw 1280 -lineh 150 \
    && rm -rf /tmp/*

WORKDIR /home/jovyan

ENV PORT=8888 NB_USER=jovyan NB_UID=1000 NB_PREFIX=/ NB_TOKEN='' NB_PASSWD=''

CMD ["bash", "-c", "\
    jupyter lab \
        --no-browser \
        --ip=0.0.0.0 \
        --port=${PORT} \
        --allow-root \
        --LabApp.token=${NB_TOKEN} \
        --LabApp.password=${NB_PASSWD} \
        --LabApp.allow_origin='*' \
        --LabApp.base_url=${NB_PREFIX} \
        --notebook-dir=/home/jovyan \
        --NotebookApp.iopub_data_rate_limit=10000000 \
        --NotebookApp.terminado_settings=\"{'shell_command': ['/usr/bin/zsh']}\" \
"]
