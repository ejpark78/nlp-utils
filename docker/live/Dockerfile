ARG BASE_IMAGE=registry.nlp-utils/crawler:base
FROM ${BASE_IMAGE}

LABEL maintainer="ejpark@ncsoft.co.kr"

ADD ssl/*.crt /usr/share/ca-certificates/

RUN echo "" >> /etc/ca-certificates.conf \
    && echo "SSLVACERT.crt" >> /etc/ca-certificates.conf \
    && echo "SSLVACERT_ECC.crt" >> /etc/ca-certificates.conf \
    && update-ca-certificates

ENV PYTHONWARNINGS "ignore:Unverified HTTPS request"

ENV CURL_CA_BUNDLE=""

ARG DOCKER_IMAGE
ARG DOCKER_TAG
ARG BUILD_DATE
ARG GIT_URL
ARG GIT_BRANCH
ARG GIT_TAG
ARG GIT_COMMIT_ID
ARG GIT_COMMIT_COUNT
ARG INSTALL_BRANCH
ARG CONFIG_BRANCH

ENV DOCKER_IMAGE=${DOCKER_IMAGE}
ENV DOCKER_TAG=${DOCKER_TAG}
ENV BUILD_DATE=${BUILD_DATE}
ENV GIT_URL=${GIT_URL}
ENV GIT_BRANCH=${GIT_BRANCH}
ENV GIT_TAG=${GIT_TAG}
ENV GIT_COMMIT_ID=${GIT_COMMIT_ID}
ENV GIT_COMMIT_COUNT=${GIT_COMMIT_COUNT}
ENV INSTALL_BRANCH=${INSTALL_BRANCH}
ENV CONFIG_BRANCH=${CONFIG_BRANCH}

RUN echo && echo "크롤러 설치 (git): ${INSTALL_BRANCH}" \
     && git clone -b ${INSTALL_BRANCH} http://ejpark:utSWJzbGBnmomJjm55Xh@galadriel02.korea.ncsoft.corp/crawler/crawler.git /tmp/crawler \
     && cd /tmp/crawler \
     && pip3 install -r requirements.txt \
     && python3 setup.py install \
     && pip3 show crawler \
     && rm -rf /tmp/*

RUN echo && echo "크롤러 config 설치: ${CONFIG_BRANCH}" \
    && git clone -b ${CONFIG_BRANCH} http://galadriel02.korea.ncsoft.corp/crawler/config.git /config

#RUN echo && echo "크롤러 설치 (pypi)" \
#    && pip3 install -U crawler \
#    && pip3 show crawler \
#    && rm -rf /root/.cache

#ENV DEBUG=1
#
#RUN mkdir -p /src
#WORKDIR /src
#
#ADD app.tar.gz /src
#
#RUN echo && echo "크롤러 설치" \
#    && pip3 install -r requirements.txt \
#    && make install \
#    && echo ${GIT_TAG}.${GIT_COMMIT_COUNT} | tee version \
#	&& python3 setup.py install \
#    && mv config /config \
#    && rm -rf /src

WORKDIR /app

