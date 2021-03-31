FROM ubuntu:20.04

LABEL maintainer="ejpark@ncsoft.co.kr"
LABEL reference="https://github.com/mviereck/dockerfile-x11docker-xfce/blob/master/Dockerfile"

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
    && apt install -yq \
        apt-transport-https \
        apt-utils \
        autoconf \
		bash \
        bison \
        build-essential \
        ca-certificates \
        crudini \
        curl \
        dpkg-dev \
        fcitx-hangul \
        firefox \
        flex \
        git \
        gnupg \
        gpg-agent \
        libcap-dev \
        libcurl4-openssl-dev \
        libdb-dev \
        libpam0g-dev \
        libssl-dev \
        libx11-dev \
        libxfixes-dev \
        libxml2-dev \
        libxrandr-dev \
        locales \
        nasm \
        openssh-client \
        pkg-config \
        pulseaudio \
        python3 \
        python3-dateutil \
        python3-dev \
        python3-lxml \
        python3-pip \
        software-properties-common \
        sudo \
        supervisor \
        tilix \
        tmux \
        tzdata \
        unzip \
        vim \
        wget \
        xauth \
        xfce4 \
        xfce4-clipman-plugin \
        xfce4-cpugraph-plugin \
        xfce4-netload-plugin \
        xfce4-screenshooter \
        xfce4-taskmanager \
        xfce4-terminal \
        xfce4-xkb-plugin \
        xorgxrdp \
        xprintidle \
        xrdp \
        xsltproc \
        zsh \
    && echo && echo "# docker/kubectl 설치" \
	&& curl -s "https://packages.cloud.google.com/apt/doc/apt-key.gpg" | apt-key add - \
	&& curl -fsSL "https://download.docker.com/linux/ubuntu/gpg" | apt-key add - \
    && apt-add-repository "deb http://apt.kubernetes.io/ kubernetes-xenial main" \
    && apt-add-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu ${APT_CODE_NAME} stable" \
    && apt update -yq ${APT_OPTS} \
    && apt install -yq ${APT_OPTS} \
        kubectl \
        docker-ce-cli \
    && echo && echo "# 폰트 초기화 & 한글 폰트 설치" \
    && apt install -yq ${APT_OPTS} \
        fonts-baekmuk \
        fonts-nanum* \
        fonts-unfonts-core \
        fonts-unfonts-extra \
    && rm -rf /usr/share/fonts/truetype/dejavu \
    && fc-cache -f -v \
    && echo && echo "# remove screen saver" \
    && apt -y purge xscreensaver \
    && echo && echo "# timezone 설정" \
    && ln -fs /usr/share/zoneinfo/Asia/Seoul /etc/localtime \
    && dpkg-reconfigure --frontend noninteractive tzdata \
    && echo && echo "# locale 생성" \
    && locale-gen "en_US.UTF-8" \
    && locale-gen "ko_KR.UTF-8" \
    && locale-gen "ko_KR.EUC-KR" \
    && update-locale LANG=ko_KR.UTF-8 \
    && dpkg-reconfigure locales \
    && uuidgen > /etc/machine-id \
    && echo && echo "# oh my zsh 설치" \
    && wget https://github.com/robbyrussell/oh-my-zsh/raw/master/tools/install.sh -O - | zsh || true \
    && cat ${HOME}/.oh-my-zsh/templates/zshrc.zsh-template | tee ${HOME}/.zshrc \
    && rm -rf ~/.oh-my-zsh/.git \
    && echo && echo "# oh my zsh plugin 설치" \
    && git clone --depth=1 https://github.com/jonmosco/kube-ps1 ~/.kube-ps1 \
    && git clone --depth=1 https://github.com/zsh-users/zsh-completions.git ~/.oh-my-zsh/plugins/zsh-completions \
    && git clone --depth=1 https://github.com/zsh-users/zsh-syntax-highlighting.git ~/.oh-my-zsh/plugins/zsh-syntax-highlighting \
    && git clone --depth=1 https://github.com/zsh-users/zsh-autosuggestions.git ~/.oh-my-zsh/plugins/zsh-autosuggestions \
    && find ~ -name .git -type d -exec rm -rf {} + \
    && echo && echo "# 저장소 정리" \
    && apt autoremove -yq \
    && rm -rf /var/cache/* /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN echo && echo "# ubuntu 사용자 추가" \
    && useradd -rm -d /home/ubuntu -s /bin/zsh -g root -G sudo -u 1001 -p "$(openssl passwd -1 ubuntu)" ubuntu \
    && echo "env -u SESSION_MANAGER -u DBUS_SESSION_BUS_ADDRESS xfce4-session" > /home/ubuntu/.xsession \
    && echo && echo "# 설정" \
    && mkdir /var/run/dbus \
    && echo && echo "# xrdp 설정" \
    && cp /etc/X11/xrdp/xorg.conf /etc/X11 \
    && sed -i "s/console/anybody/g" /etc/X11/Xwrapper.config \
    && sed -i "s/xrdp\/xorg/xorg/g" /etc/xrdp/sesman.ini \
    && adduser xrdp ssl-cert \
    && echo "env -u SESSION_MANAGER -u DBUS_SESSION_BUS_ADDRESS xfce4-session" > ~/.xsession \
    && echo "xfce4-session" > /etc/skel/.Xclients \
    && echo "export QT_XKB_CONFIG_ROOT=/usr/share/X11/locale" >> /etc/profile \
    && echo && echo "# default terminal 설정" \
    && update-alternatives --set x-terminal-emulator /usr/bin/tilix.wrapper \
    && echo && echo "# sudoers 설정" \
    && echo "ubuntu ALL=(ALL:ALL) NOPASSWD:ALL" | sudo tee -a /etc/sudoers \
    && rm -rf /etc/xrdp/rsakeys.ini /etc/xrdp/*.pem

# chrome, webdriver:
# - https://chromedriver.chromium.org/downloads
#ENV DISPLAY=:99 CHROMEDRIVER_VER=89.0.4389.23
ENV CHROMEDRIVER_VER=89.0.4389.23

RUN echo && echo "chrome, webdriver 설치" \
    && curl -k -fsSL "https://dl-ssl.google.com/linux/linux_signing_key.pub" | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | tee /etc/apt/sources.list.d/google-chrome.list \
    && apt update -yq ${APT_OPTS} \
    && apt install -yq ${APT_OPTS} \
        fonts-vlgothic \
        google-chrome-stable=89.0.4389.114-1 \
        mercurial \
        xvfb \
    && apt autoremove -yq \
    && rm -rf /var/cache/* /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VER}/chromedriver_linux64.zip" \
    && unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/ \
    && rm -rf /tmp/* /var/tmp/*

ENV PYTHONWARNINGS "ignore:Unverified HTTPS request"

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
        brotlipy \
        bs4 \
        cachelib \
        dotty_dict \
        elasticsearch \
        html5lib \
        jsonlines \
        lxml \
        psutil \
        pycurl \
        pyjwt \
        python-dateutil \
        requests \
        requests-html \
        requests-oauthlib \
        requests[security] \
        requests[socks] \
        selenium \
        selenium-wire \
        urllib3 \
    && rm -rf /tmp/*

ADD zshrc /root/.zshrc
ADD zshrc /ubuntu/.zshrc
ADD etc /etc
ADD entrypoint.sh /usr/bin/

ADD ssl/*.crt /usr/share/ca-certificates/

RUN echo "" >> /etc/ca-certificates.conf \
    && echo "SSLVACERT.crt" >> /etc/ca-certificates.conf \
    && echo "SSLVACERT_ECC.crt" >> /etc/ca-certificates.conf \
    && update-ca-certificates

ENTRYPOINT ["/usr/bin/entrypoint.sh"]


# selenium-hub : https://medium.com/@HoussemDellai/run-selenium-ui-tests-in-docker-containers-f41ae2796b8d
# https://stackoverflow.com/questions/62011537/how-can-i-run-selenium-tests-in-a-docker-container-with-a-visible-browser

