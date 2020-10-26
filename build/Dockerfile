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

ENV PORT=8888 NB_USER=jovyan NB_UID=1000 NB_PREFIX=/ NB_TOKEN='' NB_PASSWD=''
EXPOSE ${PORT}

CMD ["bash", "-c", "\
    jupyter lab \
        --no-browser \
        --ip=0.0.0.0 \
        --port=${PORT} \
        --allow-root \
        --LabApp.token=${NB_TOKEN} \
        --LabApp.password=${NB_PASSWD} \
        --LabApp.allow_origin='*' \
        --LabApp.base_url=${NB_PREFIX} \
        --notebook-dir=/home/jovyan \
        --NotebookApp.iopub_data_rate_limit=10000000 \
        --NotebookApp.terminado_settings=\"{'shell_command': ['/usr/bin/zsh']}\" \
"]

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

