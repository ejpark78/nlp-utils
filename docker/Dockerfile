FROM debian:stretch

MAINTAINER ejpark@ncsoft.co.kr

# 사용자를 root로 설정
USER root

ENV DEBIAN_FRONTEND=noninteractive
ENV HOME=/root LANG=C.UTF-8 LC_ALL=C.UTF-8


# 1. apt 저장소 변경
RUN rm -rf /var/lib/apt/lists/* \
	&& { \
		echo "deb http://ftp.daumkakao.com/debian stretch main contrib non-free"; \
		echo "deb http://ftp.daumkakao.com/debian stretch-updates main contrib non-free"; \
	} > /etc/apt/sources.list


# 2. 로케일 & 파이썬 설치
RUN apt-get update -yq \
    && apt-get install -yq --no-install-recommends \
        locales \
    && echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen \
    && echo "ko_KR.UTF-8 UTF-8" >> /etc/locale.gen \
    && echo "ko_KR.EUC-KR EUC-KR" >> /etc/locale.gen \
    && locale-gen \
    && apt-get install -yq --no-install-recommends \
        build-essential \
        ipython \
        jupyter-notebook \
        libdb-dev \
        openssh-server \
        python3 \
        python3-dateutil \
        python3-dev \
        python3-lxml \
        python3-pip \
        sqlite3 \
        supervisor \
        # 네트워크 유틸
        net-tools \
        bridge-utils \
    && mkdir -p /var/run/sshd \
    && rm -rf /var/cache/* /var/lib/apt/lists/* /tmp/* /var/tmp/*


# 3. 파이썬 라이브러리 설치
RUN pip3 install --upgrade pip setuptools
RUN pip3 install --upgrade \
        # 웹 크롤링
        bs4 \
        bsddb3 \
        requests \
        # 몽고 디비
        pymongo \
        # 메시징 서비스
        kafka-python \
        paho-mqtt \
        pyzmq \
        jupyter \
        # 엘라스틱 서치
        elasticsearch \
        python-crfsuite \
    && python3 -m ipykernel.kernelspec \
    && rm -rf $HOME/.cache


# 4. 설정 파일 복사
COPY etc/skel /root/
COPY etc/supervisor/* /etc/supervisor/conf.d/


# 5. 시스템 유틸 설치
ENV USER_INIT_DIR="/usr/local/init.d/user"
ENV ROOT_INIT_DIR="/usr/local/init.d/root"

RUN mkdir -p $USER_INIT_DIR $ROOT_INIT_DIR

COPY sbin/* /usr/local/sbin/
COPY init.d/user/* $USER_INIT_DIR/
COPY init.d/root/* $ROOT_INIT_DIR/

RUN chmod 755 /usr/local/sbin/* /usr/local/init.d/* \
    && chmod -R 777 /usr/local/sbin/* ${USER_INIT_DIR}/*

ENV NOTVISIBLE "in users profile"


# 6. host 파일 추가
COPY etc/hosts /etc/hosts.custom

# 7. 공유 폴더 위치 및 작업 위치 지정
VOLUME ["/home"]

EXPOSE 22

ENTRYPOINT ["/usr/local/sbin/entrypoint.sh"]
