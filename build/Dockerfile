ARG BASE_IMAGE=registry.nlp-utils/base/crawler:latest
FROM ${BASE_IMAGE}

LABEL maintainer="ejpark@ncsoft.co.kr"

ENV APP_HOME=/app

ADD app.tar.gz ${APP_HOME}

ADD ssl/*.crt /usr/share/ca-certificates/

RUN echo "" >> /etc/ca-certificates.conf \
    && echo "SSLVACERT.crt" >> /etc/ca-certificates.conf \
    && echo "SSLVACERT_ECC.crt" >> /etc/ca-certificates.conf \
    && update-ca-certificates

RUN echo && echo "# pip 저장소 설정" \
    && pip3 install --no-cache-dir -r ${APP_HOME}/requirements.txt

WORKDIR ${APP_HOME}

ENV CURL_CA_BUNDLE=""
ENV PYTHONPATH=${APP_HOME}

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

