ARG BASE_IMAGE=corpus:5000/base/crawler:latest
FROM ${BASE_IMAGE}

LABEL maintainer="ejpark@ncsoft.co.kr"

ARG UID=1000
ARG GID=1000
ARG USER=crawler

RUN echo "사용자 생성: ${USER}..." \
    && mkdir -p ${APP_HOME} \
	&& echo "사용자 생성..." \
	&& addgroup --gid ${GID} ${USER} \
	&& useradd --no-create-home --uid ${UID} --gid ${GID} -s /bin/bash ${USER} \
	&& chown -R ${UID}:${GID} ${APP_HOME} \
	&& usermod -G sudo ${USER} \
	&& echo "${USER} ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

ADD app.tar.gz ${APP_HOME}

ADD ssl/*.crt /usr/share/ca-certificates/

RUN echo "" >> /etc/ca-certificates.conf \
    && echo "SSLVACERT.crt" >> /etc/ca-certificates.conf \
    && echo "SSLVACERT_ECC.crt" >> /etc/ca-certificates.conf \
    && update-ca-certificates

RUN echo && echo "# pip 저장소 설정" \
    && mkdir -p ~/.pip \
    && { \
		echo "[global]"; \
		echo "timeout = 60"; \
		echo "index-url = ${PIP_MIRROR}"; \
		echo "trusted-host = ${PIP_TRUST_HOST}"; \
	} > ~/.pip/pip.conf \
    && pip3 install --no-cache-dir -r /usr/local/app/requirements.txt

WORKDIR ${APP_HOME}

ENV CURL_CA_BUNDLE=""
ENV PYTHONPATH=${APP_HOME}
