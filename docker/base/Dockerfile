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
        apt-transport-https \
        apt-utils \
		bash \
        bridge-utils \
        build-essential \
        ca-certificates \
        curl \
        git \
        gnupg \
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
        unzip \
        zsh \
    && apt install -yq ${APT_OPTS} \
        xorg-video-abi-24 \
        xserver-xorg-core \
        xserver-xorg-input-all \
        xrdp \
        xorgxrdp \
        freerdp2-x11 \
    && echo && echo "# xrdp 설정" \
    && adduser xrdp ssl-cert \
    && echo env -u SESSION_MANAGER -u DBUS_SESSION_BUS_ADDRESS cinnamon-session > ~/.xsession \
    && echo && echo "# timezone 설정" \
    && ln -fs /usr/share/zoneinfo/Asia/Seoul /etc/localtime \
    && dpkg-reconfigure --frontend noninteractive tzdata \
    && echo && echo "# oh my zsh 설치" \
    && wget https://github.com/robbyrussell/oh-my-zsh/raw/master/tools/install.sh -O - | zsh || true \
    && apt autoremove -yq \
    && rm -rf /var/cache/* /var/lib/apt/lists/* /tmp/* /var/tmp/*

# chrome, webdriver:
# - https://chromedriver.chromium.org/downloads
# - https://stynxh.github.io/2020-06-21-Install-Google-Chrome-on-Ubuntu-linux-from-command-line-kor/
# - https://stynxh.github.io/2019-10-09-Set-Selenium-and-Chrome-browser-in-Docker-korean/
# - https://stackoverflow.com/questions/45323271/how-to-run-selenium-with-chrome-in-docker
ENV DISPLAY=:99 CHROMEDRIVER_VER=88.0.4324.96

RUN echo && echo "chrome, webdriver 설치" \
    && curl -k -fsSL https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | tee /etc/apt/sources.list.d/google-chrome.list \
    && apt update -yq ${APT_OPTS} \
    && apt install -yq ${APT_OPTS} \
        fonts-vlgothic \
        google-chrome-stable \
        mercurial \
        xvfb \
    && apt autoremove -yq \
    && rm -rf /var/cache/* /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && google-chrome-stable --version \
    && wget -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VER}/chromedriver_linux64.zip \
    && unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/ \
    && rm -rf /tmp/* /var/tmp/*

RUN echo && echo "nodejs 설치" \
    && curl -sL https://deb.nodesource.com/setup_14.x | bash - \
    && apt update -yq ${APT_OPTS} \
    && apt install -yq ${APT_OPTS} \
        nodejs \
    && echo && echo "# 저장소 정리" \
    && rm -rf /var/cache/* /var/lib/apt/lists/* /tmp/* /var/tmp/*

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
        PySocks \
        PyYAML \
        boto3 \
        brotlipy \
        bs4 \
        cachelib \
        dotty_dict \
        elasticsearch \
        html5lib \
        jsonlines \
        lxml \
        minio \
        openpyxl \
        pandas \
        psutil \
        pycurl \
        pyjwt \
        python-dateutil \
        qgrid \
        requests \
        requests-html \
        requests-oauthlib \
        requests[security] \
        requests[socks] \
        selenium \
        selenium-wire \
        urllib3 \
        xlsxwriter \
    && rm -rf /tmp/*

RUN echo && echo "# jupyter 설치" \
    && pip3 install --upgrade --no-cache-dir \
		autopep8 \
		bash_kernel \
        jupyter \
        jupyterlab \
        jupyterthemes \
        sshkernel \
    && rm -rf /tmp/*

RUN echo && echo "jupyter kernel 설치" \
    && python3 -m sshkernel install \
    && python3 -m bash_kernel.install

RUN echo && echo "nbextension enable 설정" \
	&& jupyter nbextension enable --py --sys-prefix qgrid \
    && jupyter nbextension enable --py --sys-prefix widgetsnbextension \
	\
    && jupyter serverextension enable --py jupyterlab --sys-prefix \
	\
	&& echo && echo "jupyter notebook 테마 설정" \
	&& jt -t monokai -fs 11 -tfs 11 -nfs 11 -ofs 11 -cellw 980 -T -f hack -N -cellw 1280 -lineh 150

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

# selenium-hub : https://medium.com/@HoussemDellai/run-selenium-ui-tests-in-docker-containers-f41ae2796b8d
# https://stackoverflow.com/questions/62011537/how-can-i-run-selenium-tests-in-a-docker-container-with-a-visible-browser

