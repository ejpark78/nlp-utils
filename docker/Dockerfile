ARG BASE_IMAGE=registry.nlp-utils/base/crawler:latest
FROM ${BASE_IMAGE}

LABEL maintainer="ejpark@ncsoft.co.kr"

ADD ssl/*.crt /usr/share/ca-certificates/

RUN echo "" >> /etc/ca-certificates.conf \
    && echo "SSLVACERT.crt" >> /etc/ca-certificates.conf \
    && echo "SSLVACERT_ECC.crt" >> /etc/ca-certificates.conf \
    && update-ca-certificates

ENV PYTHONWARNINGS "ignore:Unverified HTTPS request"

RUN mkdir -p /src
WORKDIR /src

ADD app.tar.gz /src
RUN echo && echo "크롤러 설치" \
    && pip3 install -r requirements.txt \
    && make install \
    && mv crawler/config / \
    && rm -rf /src

WORKDIR /app

ENV CURL_CA_BUNDLE=""

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

