ARG BASE_IMAGE=x11:core
FROM ${BASE_IMAGE}

LABEL maintainer="ejpark@ncsoft.co.kr"

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

RUN echo && echo "# cinnamon 설치" \
    && apt update -yq ${APT_OPTS} \
    && apt install -yq ${APT_OPTS} \
        apt-transport-https \
        apt-utils \
        autoconf \
        dbus-x11 \
        dpkg-dev \
        gpg-agent \
        pkg-config \
        xserver-xorg-dev \
        cinnamon-desktop-environment \
    \
    && echo && echo "# xrdp 설정" \
    && echo "env -u SESSION_MANAGER -u DBUS_SESSION_BUS_ADDRESS cinnamon-session" > ~/.xsession \
    && echo "cinnamon-session" > /etc/skel/.Xclients \
    \
    && echo && echo "# 저장소 정리" \
    && apt purge -yq \
        apt-transport-https \
        apt-utils \
        autoconf \
        dpkg-dev \
        gpg-agent \
        pkg-config \
        xscreensaver \
    && apt autoremove -yq \
    && rm -rf /var/cache/* /var/lib/apt/lists/* /tmp/* /var/tmp/*

EXPOSE 3389 9001

CMD ["supervisord"]
