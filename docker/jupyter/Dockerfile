ARG BASE_IMAGE=registry.nlp-utils/crawler-dev:dev
FROM ${BASE_IMAGE}

LABEL maintainer="ejpark@ncsoft.co.kr"

# 파이썬 라이브러리 설치
RUN echo && echo "# pip 저장소 설정" \
    && mkdir -p ~/.pip \
    && { \
		echo "[global]"; \
		echo "timeout = 60"; \
		echo "index-url = ${PIP_MIRROR}"; \
		echo "trusted-host = ${PIP_TRUST_HOST}"; \
	} > ~/.pip/pip.conf \
    && echo && echo "# jupyter 설치" \
    && pip3 install --upgrade --no-cache-dir \
		autopep8 \
		bash_kernel \
        jupyter \
        jupyterlab \
        jupyterthemes \
        sshkernel \
        qgrid \
    && rm -rf /tmp/*

RUN echo && echo "jupyter kernel 설치" \
    && python3 -m sshkernel install \
    && python3 -m bash_kernel.install

RUN echo && echo "nbextension enable 설정" \
	&& jupyter nbextension enable --py --sys-prefix qgrid \
    && jupyter nbextension enable --py --sys-prefix widgetsnbextension \
	\
    && jupyter serverextension enable --py jupyterlab --sys-prefix \
	\
	&& echo && echo "jupyter notebook 테마 설정" \
	&& jt -t monokai -fs 11 -tfs 11 -nfs 11 -ofs 11 -cellw 980 -T -f hack -N -cellw 1280 -lineh 150

RUN echo && echo "크롤러 config 설치" \
    && rm -rf /config \
    && git clone http://galadriel02.korea.ncsoft.corp/crawler/config.git /config

WORKDIR /home/jovyan

ENV PORT=8888 NB_USER=jovyan NB_UID=1000 NB_PREFIX=/ NB_TOKEN='' NB_PASSWD=''

CMD ["bash", "-c", "\
    jupyter lab \
        --no-browser \
        --ip=0.0.0.0 \
        --port=${PORT} \
        --allow-root \
        --notebook-dir=/home/jovyan \
        --ServerApp.token=${NB_TOKEN} \
        --ServerApp.password=${NB_PASSWD} \
        --ServerApp.allow_origin='*' \
        --ServerApp.base_url=${NB_PREFIX} \
        --ServerApp.iopub_data_rate_limit=10000000 \
        --ServerApp.terminado_settings=\"{'shell_command': ['/bin/bash']}\" \
"]

ADD ssl/*.crt /usr/share/ca-certificates/

RUN echo "" >> /etc/ca-certificates.conf \
    && echo "SSLVACERT.crt" >> /etc/ca-certificates.conf \
    && echo "SSLVACERT_ECC.crt" >> /etc/ca-certificates.conf \
    && update-ca-certificates

ENV CURL_CA_BUNDLE=""
