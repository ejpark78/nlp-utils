FROM ubuntu:20.04

LABEL maintainer="ejpark@ncsoft.co.kr"
LABEL reference="https://github.com/danielguerra69/ubuntu-xrdp/blob/master/Dockerfile"

ENV DEBIAN_FRONTEND=noninteractive
ENV HOME=/root LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV NOTVISIBLE "in users profile"

ARG APT_CODE_NAME=focal
ARG APT_MIRROR=http://mirror.kakao.com/ubuntu
ARG PIP_TRUST_HOST=mirror.kakao.com
ARG PIP_MIRROR=http://mirror.kakao.com/pypi/simple

ENV APT_OPTS="--no-install-suggests --no-install-recommends"
ENV PYTHONWARNINGS "ignore:Unverified HTTPS request"

USER root
WORKDIR $HOME

# chrome, webdriver:
# - https://chromedriver.chromium.org/downloads
ENV CHROMEDRIVER_VER=89.0.4389.23

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
    && apt update -yq ${APT_OPTS} \
    && apt install -yq ${APT_OPTS} \
        curl \
        gnupg \
        software-properties-common \
	\
	&& curl -k -fsSL "https://download.docker.com/linux/ubuntu/gpg" | apt-key add - \
    && apt-add-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu ${APT_CODE_NAME} stable" \
	\
	&& curl -k -fsSL "https://packages.cloud.google.com/apt/doc/apt-key.gpg" | apt-key add - \
    && apt-add-repository "deb http://apt.kubernetes.io/ kubernetes-xenial main" \
	\
    && curl -k -fsSL "https://dl-ssl.google.com/linux/linux_signing_key.pub" | apt-key add - \
    && apt-add-repository "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" \
    \
    && apt update -yq ${APT_OPTS} \
    && apt install -yq \
        apt-transport-https \
        apt-utils \
        autoconf \
        bash \
        build-essential \
        ca-certificates \
        crudini \
        dpkg-dev \
        fcitx-hangul \
        fonts-nanum* \
        fonts-unfonts-core \
        fonts-unfonts-extra \
        fonts-vlgothic \
        git \
        google-chrome-stable=89.0.4389.114-1 \
        gpg-agent \
        htop \
        kubectl \
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
        pkg-config \
        python3 \
        python3-dateutil \
        python3-dev \
        python3-pip \
        sqlite \
        sudo \
        supervisor \
        tilix \
        tmux \
        tzdata \
        unzip \
        uuid-runtime \
        vim \
        wget \
        xauth \
        xfce4 \
        xfce4-clipman-plugin \
        xfce4-cpugraph-plugin \
        xfce4-netload-plugin \
        xfce4-screenshooter \
        xfce4-taskmanager \
        xfce4-xkb-plugin \
        xrdp \
        xvfb \
        zsh \
    \
    && echo && echo "# 폰트 초기화" \
    && rm -rf /usr/share/fonts/truetype/dejavu \
    && fc-cache -f -v \
    \
    && echo && echo "# timezone 설정" \
    && ln -fs /usr/share/zoneinfo/Asia/Seoul /etc/localtime \
    && dpkg-reconfigure --frontend noninteractive tzdata \
    \
    && echo && echo "# locale 생성" \
    && locale-gen "en_US.UTF-8" \
    && locale-gen "ko_KR.UTF-8" \
    && locale-gen "ko_KR.EUC-KR" \
    && update-locale LANG=ko_KR.UTF-8 \
    && dpkg-reconfigure locales \
    && uuidgen > /etc/machine-id \
    \
    && echo && echo "# 파이썬 기본 유틸 설치" \
    && pip3 install --upgrade \
        pip \
        setuptools \
        wheel \
    \
    && echo && echo "# 파이썬 라이브러리 설치" \
    && pip3 install --upgrade \
        brotlipy \
        bs4 \
        cachelib \
        dotty_dict \
        elasticsearch \
        html5lib \
        jsonfinder \
        jsonlines \
        lxml \
        pycurl \
        pyjwt \
        PyMySQL \
        PySocks \
        python-dateutil \
        PyYAML \
        requests \
        requests-html \
        requests-oauthlib \
        requests[security] \
        requests[socks] \
        selenium \
        selenium-wire \
        urllib3 \
    \
    && echo && echo "# 저장소 정리" \
    && apt purge -yq \
        apt-transport-https \
        apt-utils \
        autoconf \
        build-essential \
        dpkg-dev \
        gnome-terminal \
        gpg-agent \
        pkg-config \
        software-properties-common \
        uuid-runtime \
        xscreensaver \
    && apt autoremove -yq \
    && rm -rf /var/cache/* /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN echo && echo "# webdriver 설치" \
    && wget "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VER}/chromedriver_linux64.zip"  \
        -O /tmp/chromedriver.zip \
    && unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/ \

RUN echo && echo "# xrdp 설정" \
    && mkdir /var/run/dbus \
    && cp /etc/X11/xrdp/xorg.conf /etc/X11 \
    && sed -i "s/xrdp\/xorg/xorg/g" /etc/xrdp/sesman.ini \
    && sed -i "s/console/anybody/g" /etc/X11/Xwrapper.config \
    && echo "env -u SESSION_MANAGER -u DBUS_SESSION_BUS_ADDRESS xfce4-session" > ~/.xsession \
    && echo "xfce4-session" > /etc/skel/.Xclients \
    && echo "export QT_XKB_CONFIG_ROOT=/usr/share/X11/locale" >> /etc/profile \
    && rm -rf /etc/xrdp/rsakeys.ini /etc/xrdp/*.pem

ADD etc /etc
ADD zshrc /root/.zshrc
ADD zshrc /home/ubuntu/.zshrc
ADD entrypoint.sh /usr/bin/

ADD ssl/*.crt /usr/share/ca-certificates/

RUN echo && echo "# ubuntu 사용자 추가" \
    && groupadd -g 1000 ubuntu \
    && useradd -rm -d /home/ubuntu -s /bin/zsh -G sudo -g ubuntu -u 1000 -p "$(openssl passwd -1 ubuntu)" ubuntu \
    && echo "env -u SESSION_MANAGER -u DBUS_SESSION_BUS_ADDRESS xfce4-session" > /home/ubuntu/.xsession \
    && echo "ubuntu ALL=(ALL:ALL) NOPASSWD:ALL" | sudo tee -a /etc/sudoers \
    \
    && echo && echo "# oh my zsh 설치" \
    && wget "https://github.com/robbyrussell/oh-my-zsh/raw/master/tools/install.sh" -O - | zsh || true \
    && rm -rf ~/.oh-my-zsh/.git \
    && mv ~/.oh-my-zsh /home/ubuntu/ \
    \
    && echo && echo "# oh my zsh plugin 설치" \
    && git clone --depth=1 "https://github.com/jonmosco/kube-ps1" /home/ubuntu/.kube-ps1 \
    && git clone --depth=1 "https://github.com/zsh-users/zsh-completions.git" /home/ubuntu/.oh-my-zsh/plugins/zsh-completions \
    && git clone --depth=1 "https://github.com/zsh-users/zsh-syntax-highlighting.git" /home/ubuntu/.oh-my-zsh/plugins/zsh-syntax-highlighting \
    && git clone --depth=1 "https://github.com/zsh-users/zsh-autosuggestions.git" /home/ubuntu/.oh-my-zsh/plugins/zsh-autosuggestions \
    && find ~ -name .git -type d -exec rm -rf {} + \
    \
    && chown -R ubuntu:ubuntu /home/ubuntu

ARG HELM_VER="v3.5.2"
ARG K9S_VER="v0.24.6"
ARG STERN_VER="1.11.0"

RUN echo && echo "# helm 설치" \
	&& wget -O /tmp/helm.tar.gz "https://get.helm.sh/helm-${HELM_VER}-linux-amd64.tar.gz" \
    && tar xvfz /tmp/helm.tar.gz -C /tmp \
    && mv /tmp/linux-amd64/helm /usr/bin/ \
    \
    && echo && echo "# k9s 설치" \
    && wget -O /tmp/k9s.tar.gz "https://github.com/derailed/k9s/releases/download/${K9S_VER}/k9s_Linux_x86_64.tar.gz" \
    && tar xvfz /tmp/k9s.tar.gz -C /tmp \
    && mv /tmp/k9s /usr/bin/ \
    \
    && echo && echo "# stern 설치" \
    && wget -O /usr/bin/stern "https://github.com/wercker/stern/releases/download/${STERN_VER}/stern_linux_amd64" \
    && chmod +x /usr/bin/stern \
    \
    && echo && echo "# krew 설치" \
    && wget -O /tmp/krew.tar.gz "https://github.com/kubernetes-sigs/krew/releases/latest/download/krew.tar.gz" \
    && tar zxvf /tmp/krew.tar.gz -C /tmp \
    && mv /tmp/krew-linux_amd64 /usr/bin/krew \
    && chmod +x /usr/bin/krew \
    && krew install krew \
    && export PATH="${KREW_ROOT:-$HOME/.krew}/bin:$PATH" \
    && kubectl krew update \
    && kubectl krew install ctx \
    && kubectl krew install ns \
    && kubectl krew install konfig \
    && rm -rf /var/cache/* /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN echo "" >> /etc/ca-certificates.conf \
    && echo "SSLVACERT.crt" >> /etc/ca-certificates.conf \
    && echo "SSLVACERT_ECC.crt" >> /etc/ca-certificates.conf \
    && update-ca-certificates

ENTRYPOINT ["/usr/bin/entrypoint.sh"]
