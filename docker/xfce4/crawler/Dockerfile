ARG BASE_IMAGE=xfce4:core
FROM ${BASE_IMAGE}

LABEL maintainer="ejpark@ncsoft.co.kr"

USER root
WORKDIR $HOME

RUN echo && echo "# python 설치" \
    && apt update -yq ${APT_OPTS} \
    && apt install -yq ${APT_OPTS} \
        build-essential \
        ca-certificates \
        python3 \
        python3-dev \
        python3-pip \
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
        build-essential \
    && apt autoremove -yq \
    && rm -rf /var/cache/* /var/lib/apt/lists/* /tmp/* /var/tmp/*

CMD ["supervisord"]

