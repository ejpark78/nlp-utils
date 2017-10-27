FROM debian:stretch

LABEL maintainer="ejpark@ncsoft.co.kr"


# 사용자를 root로 설정
USER root

ENV DEBIAN_FRONTEND=noninteractive
ENV HOME=/root LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV NOTVISIBLE "in users profile"


# 1. apt 저장소 변경
RUN rm -rf /var/lib/apt/lists/* \
	&& { \
		echo "deb http://frodo/debian stretch main contrib non-free"; \
		echo "deb http://frodo/debian stretch-updates main contrib non-free"; \
	} > /etc/apt/sources.list \
    && echo "172.20.51.91 frodo" >> /etc/hosts \
    \
    && apt-get update -yq \
    \
    && echo && echo "# 2. 로케일 & 파이썬 설치" \
    \
    && apt-get install -yq --no-install-recommends \
        locales \
    && echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen \
    && echo "ko_KR.UTF-8 UTF-8" >> /etc/locale.gen \
    && echo "ko_KR.EUC-KR EUC-KR" >> /etc/locale.gen \
    && locale-gen \
    && apt-get install -yq --no-install-recommends \
        bridge-utils \
        build-essential \
        cron \
        ipython \
        libdb-dev \
        net-tools \
        openssh-server \
        python3 \
        python3-dateutil \
        python3-dev \
        python3-lxml \
        python3-pip \
        sqlite3 \
        supervisor \
        sudo \
    \
    && echo && echo "# pycharm 의존 라이브러리 " \
    && apt-get install -yq --no-install-recommends \
        git \
        fonts-nanum \
        fonts-nanum-coding \
        fonts-unfonts-core \
        hunspell-ko \
        iceweasel \
        xauth \
        xfonts-100dpi \
        xfonts-75dpi \
        xfonts-cyrillic \
        xz-utils \
        libxrender1 \
        libxtst6 \
        libfreetype6 \
    && rm -rf /var/cache/* /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    \
    && echo && echo "# ssh 설정" \
    && mkdir -p /var/run/sshd \
    && sed -i 's/^mesg/# mesg/' /root/.profile \
    && echo "export VISIBLE=now" >> /etc/profile \
    && touch /root/.Xauthority \
    && sed -i 's/^#X11UseLocalhost yes/X11UseLocalhost no/' /etc/ssh/sshd_config \
    && echo "Ciphers arcfour,blowfish-cbc" >> /etc/ssh/sshd_config \
    \
    && echo && echo "# 3. 파이썬 라이브러리 설치" \
    && mkdir -p ~/.pip \
    && { \
		echo "[global]"; \
		echo "timeout = 60"; \
		echo "index-url = http://frodo:3141/root/pypi"; \
		echo "[install]"; \
		echo "trusted-host = frodo"; \
	} > ~/.pip/pip.conf \
    \
    && pip3 install --upgrade \
        pip \
        setuptools \
        wheel \
    && sync \
    \
    && pip3 install --upgrade \
        bs4 \
        bsddb3 \
        requests \
        pymongo \
        kafka-python \
        paho-mqtt \
        pyzmq \
        jupyter \
        elasticsearch \
        python-crfsuite \
        cython \
    && python3 -m ipykernel.kernelspec \
    && rm -rf $HOME/.cache \
    \
    && mkdir -p /root/users


# 4. 설정 파일 복사
ENV ROOT_INIT_DIR="/usr/local/init.d/root"

RUN mkdir -p $ROOT_INIT_DIR

COPY etc/skel /root/
COPY etc/supervisor/* /etc/supervisor/conf.d/

COPY sbin/* /usr/local/sbin/

COPY init.d/root/* $ROOT_INIT_DIR/

COPY etc/*.extra /etc/

RUN chmod 755 /usr/local/sbin/* /usr/local/init.d/* \
    && chmod -R 777 /usr/local/sbin/* $ROOT_INIT_DIR/*


# 7. 공유 폴더 위치 및 작업 위치 지정
VOLUME ["/home"]

EXPOSE 22

ENTRYPOINT ["/usr/local/sbin/entrypoint.sh"]
