ARG BASE_IMAGE=x11:core
FROM ${BASE_IMAGE}

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

RUN echo && echo "# xfce4 설치" \
    && apt update -yq ${APT_OPTS} \
    && apt install -yq ${APT_OPTS} \
        apt-transport-https \
        apt-utils \
        autoconf \
        dbus-x11 \
        dpkg-dev \
        gpg-agent \
        pkg-config \
        xfce4 \
        xfce4-clipman-plugin \
        xfce4-cpugraph-plugin \
        xfce4-netload-plugin \
        xfce4-screenshooter \
        xfce4-taskmanager \
        xfce4-xkb-plugin \
    \
    && echo && echo "# xrdp 설정" \
    && echo "env -u SESSION_MANAGER -u DBUS_SESSION_BUS_ADDRESS xfce4-session" > ~/.xsession \
    && echo "xfce4-session" > /etc/skel/.Xclients \
    \
    && echo && echo "# 저장소 정리" \
    && apt purge -yq \
        apt-transport-https \
        apt-utils \
        autoconf \
        dpkg-dev \
        gnome-terminal \
        gpg-agent \
        pkg-config \
        xscreensaver \
    && apt autoremove -yq \
    && rm -rf /var/cache/* /var/lib/apt/lists/* /tmp/* /var/tmp/*

EXPOSE 22

CMD ["supervisord"]
