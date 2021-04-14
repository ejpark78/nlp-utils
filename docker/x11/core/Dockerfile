FROM ubuntu:20.04

LABEL maintainer="ejpark@ncsoft.co.kr"
LABEL reference="https://github.com/danielguerra69/ubuntu-xrdp/blob/master/Dockerfile"

ENV DEBIAN_FRONTEND=noninteractive
ENV HOME=/root LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV USER_HOME=/home/ubuntu USER_NAME=ubuntu USER_PASSWD=ubuntu USER_GROUP=ubuntu
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
	&& echo && echo "# chrome, k8s, docker 저장소 설정" \
    && apt update -yq ${APT_OPTS} \
    && apt install -yq ${APT_OPTS} \
        bash \
        ca-certificates \
        curl \
        dconf-cli \
        fontconfig \
        fonts-liberation \
        fonts-nanum* \
        fonts-unfonts-core \
        fonts-unfonts-extra \
        fonts-vlgothic \
        git \
        gnupg \
        gpg \
        language-pack-gnome-ko \
        language-pack-ko \
        less \
        libcurl4-openssl-dev \
        libdb-dev \
        libssl-dev \
        locales \
        python3 \
        python3-dev \
        software-properties-common \
        sqlite \
        sudo \
        supervisor \
        tmux \
        tzdata \
        unzip \
        vim \
        wget \
        zsh \
	\
    && echo && echo "# apt repo 등록" \
	&& curl -k -fsSL "https://download.docker.com/linux/ubuntu/gpg" | apt-key add - \
    && apt-add-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu ${APT_CODE_NAME} stable" \
	\
	&& curl -k -fsSL "https://packages.cloud.google.com/apt/doc/apt-key.gpg" | apt-key add - \
    && apt-add-repository "deb http://apt.kubernetes.io/ kubernetes-xenial main" \
	\
    && curl -k -fsSL "https://dl-ssl.google.com/linux/linux_signing_key.pub" | apt-key add - \
    && apt-add-repository "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" \
    \
    && curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /etc/apt/trusted.gpg.d/microsoft.gpg \
    && sudo sh -c 'echo "deb [arch=amd64] https://packages.microsoft.com/repos/vscode stable main" > /etc/apt/sources.list.d/vscode.list' \
    \
    && echo && echo "# 폰트 초기화" \
    && rm -rf /usr/share/fonts/truetype/dejavu \
    && fc-cache -f -v -r \
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
    && apt purge -yq ${APT_OPTS} \
        gpg \
        software-properties-common \
        tzdata \
    && apt autoremove -yq \
    && rm -rf /tmp/* /var/cache/* /var/lib/apt/lists/* /var/tmp/*

RUN echo && echo "# xserver, xrdp 설치" \
    && apt update -yq ${APT_OPTS} \
    && apt install -yq ${APT_OPTS} \
        apt-transport-https \
        apt-utils \
        autoconf \
        crudini \
        dbus-x11 \
        dpkg-dev \
        gpg-agent \
        libcap-dev \
        libpam0g-dev \
        libx11-dev \
        libxfixes-dev \
        libxml2-dev \
        libxrandr-dev \
        nemo \
        openssh-server \
        pkg-config \
        pulseaudio \
        tilix \
        uuid-runtime \
        xauth \
        xorgxrdp \
        xrdp \
        xserver-xorg-core \
        xserver-xorg-legacy \
        xvfb \
    \
    && echo && echo "# xrdp 설정" \
    && mkdir /var/run/dbus \
    && uuidgen > /etc/machine-id \
    && cp /etc/X11/xrdp/xorg.conf /etc/X11 \
    && sed -i "s/xrdp\/xorg/xorg/g" /etc/xrdp/sesman.ini \
    && sed -i "s/console/anybody/g" /etc/X11/Xwrapper.config \
    && echo "export QT_XKB_CONFIG_ROOT=/usr/share/X11/locale" >> /etc/profile \
    \
    && echo && echo "# xrdp ssl 설정" \
    && rm -rf /etc/xrdp/rsakeys.ini /etc/xrdp/*.pem \
    && xrdp-keygen xrdp auto \
    && openssl req -x509 -newkey rsa:2048 -nodes -days 365 \
        -out /etc/xrdp/cert.pem -keyout /etc/xrdp/key.pem \
        -subj "/C=US/ST=Some State/L=Some City/O=Some Org/OU=Some Unit/CN=Terminalserver" \
    && crudini --set /etc/xrdp/xrdp.ini Globals port tcp://.:3389 \
    && crudini --set /etc/xrdp/xrdp.ini Globals security_layer tls \
    && crudini --set /etc/xrdp/xrdp.ini Globals certificate /etc/xrdp/cert.pem \
    && crudini --set /etc/xrdp/xrdp.ini Globals key_file /etc/xrdp/key.pem \
    && crudini --set /etc/xrdp/xrdp.ini Xorg username ${USER_NAME} \
    && crudini --set /etc/xrdp/xrdp.ini Xorg password ${USER_PASSWD} \
    \
    && echo && echo "# tilix vte 설정" \
    && ln -s /etc/profile.d/vte-*.sh /etc/profile.d/vte.sh \
    \
    && echo && echo "# ssh server 설정" \
    && mkdir -p /run/sshd \
    \
    && echo && echo "# 저장소 정리" \
    && apt purge -yq \
        apt-transport-https \
        apt-utils \
        autoconf \
        crudini \
        dpkg-dev \
        gnome-terminal \
        gpg-agent \
        pkg-config \
        thunar \
        uuid-runtime \
        xscreensaver \
    && apt autoremove -yq \
    && rm -rf /tmp/* /var/cache/* /var/lib/apt/lists/* /var/tmp/*

RUN echo && echo "# fcitx hangul 설치" \
    && apt update -yq ${APT_OPTS} \
    && apt install -yq \
        fcitx-hangul \
    && echo && echo "# 저장소 정리" \
    && apt autoremove -yq \
    && rm -rf /tmp/* /var/cache/* /var/lib/apt/lists/* /var/tmp/*

RUN echo && echo "# chrome 설치" \
    && apt update -yq ${APT_OPTS} \
    && apt install -yq \
        firefox \
        google-chrome-stable \
    \
    && echo && echo "# webdriver 설치" \
    && wget --no-check-certificate "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VER}/chromedriver_linux64.zip"  \
        -O /tmp/chromedriver.zip \
    && unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/ \ \
    && echo && echo "# 저장소 정리" \
    && apt purge -yq \
        cpp \
        cpp-9 \
    && apt autoremove -yq \
    && rm -rf /tmp/* /var/cache/* /var/lib/apt/lists/* /var/tmp/*

ADD etc /etc
ADD bin /usr/bin

RUN echo && echo "# ${USER_NAME} 사용자 추가" \
    && groupadd -g 999 docker \
    && groupadd -g 1000 ${USER_GROUP} \
    && useradd -rm -d ${USER_HOME} -s /bin/zsh -G sudo -g ${USER_GROUP} -u 1000 \
        -p "$(openssl passwd -1 ${USER_PASSWD})" ${USER_NAME} \
    && usermod -aG root ${USER_NAME} \
    && usermod -aG docker ${USER_NAME} \
    \
    && echo "env -u SESSION_MANAGER -u DBUS_SESSION_BUS_ADDRESS xfce4-session" > ${USER_HOME}/.xsession \
    && echo "${USER_NAME} ALL=(ALL:ALL) NOPASSWD:ALL" | sudo tee -a /etc/sudoers \
    \
    && echo && echo "# oh my zsh 설치" \
    && wget "https://github.com/robbyrussell/oh-my-zsh/raw/master/tools/install.sh" -O - | zsh || true \
    && rm -rf ~/.oh-my-zsh/.git \
    && mv ~/.oh-my-zsh ${USER_HOME}/ \
    \
    && echo && echo "# oh my zsh plugin 설치" \
    && git clone --depth=1 "https://github.com/jonmosco/kube-ps1" ${USER_HOME}/.kube-ps1 \
    && git clone --depth=1 "https://github.com/zsh-users/zsh-completions.git" ${USER_HOME}/.oh-my-zsh/plugins/zsh-completions \
    && git clone --depth=1 "https://github.com/zsh-users/zsh-syntax-highlighting.git" ${USER_HOME}/.oh-my-zsh/plugins/zsh-syntax-highlighting \
    && git clone --depth=1 "https://github.com/zsh-users/zsh-autosuggestions.git" ${USER_HOME}/.oh-my-zsh/plugins/zsh-autosuggestions \
    && find ~ -name .git -type d -exec rm -rf {} + \
    \
    && echo && echo "# zshrc 설정" \
    && mv /etc/zshrc ${USER_HOME}/.zshrc \
    \
    && echo && echo "# ssh 설정" \
    && mv /etc/.ssh ${USER_HOME}/.ssh \
    && cat ${USER_HOME}/.ssh/id_rsa > ${USER_HOME}/.ssh/${USER_NAME}.pem \
    && cat ${USER_HOME}/.ssh/id_rsa.pub > ${USER_HOME}/.ssh/authorized_keys \
    && chmod 700 ${USER_HOME}/.ssh \
    && chmod 600 ${USER_HOME}/.ssh/id_rsa \
    && chmod 644 ${USER_HOME}/.ssh/id_rsa.pub \
    && chmod 600 ${USER_HOME}/.ssh/authorized_keys \
    && sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config \
    \
    && echo && echo "# ${USER_NAME} 퍼미션 변경" \
    && chown -R ${USER_NAME}:${USER_GROUP} ${USER_HOME}

RUN echo && echo "# SSL 설치" \
    && apt update -yq ${APT_OPTS} \
    && apt install -yq ${APT_OPTS} \
        libnss3-tools \
    \
    && mv /etc/web_ssl/*.crt /usr/share/ca-certificates/ \
    && echo "" >> /etc/ca-certificates.conf \
    && echo "SSLVACERT.crt" >> /etc/ca-certificates.conf \
    && echo "SSLVACERT_ECC.crt" >> /etc/ca-certificates.conf \
    && update-ca-certificates \
    \
    && echo && echo "# chrome 에 ssl 등록 " \
    && mkdir -p ${USER_HOME}/.pki/nssdb \
    && certutil -d ${USER_HOME}/.pki/nssdb -N \
    && certutil -d sql:${USER_HOME}/.pki/nssdb -A -t TC -n "CAcert.org" -i /usr/share/ca-certificates/SSLVACERT.crt \
    && certutil -d sql:${USER_HOME}/.pki/nssdb -A -t TC -n "CAcert.org Class 3" -i /usr/share/ca-certificates/SSLVACERT_ECC.crt \
    && chown -R ${USER_NAME}:${USER_GROUP} ${USER_HOME}/.pki \
    \
    && echo && echo "# 저장소 정리" \
    && apt autoremove -yq \
    && rm -rf /tmp/* /var/cache/* /var/lib/apt/lists/* /var/tmp/*

EXPOSE 22

CMD ["supervisord"]
