ARG BASE_IMAGE=tensorflow/tensorflow:2.3.0

FROM ${BASE_IMAGE}

# https://blog.realkinetic.com/building-minimal-docker-containers-for-python-applications-37d0272c52f3

LABEL author="박은진<ejpark78@gmail.com>"

ENV DEBIAN_FRONTEND=noninteractive
ENV HOME=/root LANG=C.UTF-8 LC_ALL=C.UTF-8 LANGUAGE=ko_KR:en

ARG APT_CODE_NAME=bionic
ARG APT_MIRROR=http://mirror.kakao.com/ubuntu
ARG PIP_MIRROR=http://mirror.kakao.com/pypi/simple
ARG PIP_TRUST_HOST=mirror.kakao.com

USER root
ENV APT_OPTS="--no-install-suggests --no-install-recommends"

RUN echo && echo "# APT MIRROR 변경: ${APT_MIRROR}" \
	&& { \
		echo "deb ${APT_MIRROR} ${APT_CODE_NAME} main restricted universe multiverse"; \
		echo "deb ${APT_MIRROR} ${APT_CODE_NAME}-updates main restricted universe multiverse"; \
		echo "deb ${APT_MIRROR} ${APT_CODE_NAME}-backports main restricted universe multiverse"; \
	} > /etc/apt/sources.list \
    \
	&& { \
		echo "Acquire::https {"; \
		echo "  Verify-Peer false;"; \
		echo "  Verify-Host false;"; \
		echo "};"; \
	} > /etc/apt/apt.conf.d/mirror.conf \
    \
    && apt update -yq ${APT_OPTS} \
    && apt install -yq ${APT_OPTS} \
        ca-certificates \
        python3 \
        python3-dev \
        python3-pip \
        libcurl4-openssl-dev \
        libgoogle-perftools-dev \
        libssl-dev \
        libxml2-dev \
        libxslt-dev \
    && echo && echo "# 저장소 정리" \
    && rm -rf /var/cache/* /var/lib/apt/lists/* /tmp/* /var/tmp/*

# 파이썬 라이브러리 설치
RUN echo && echo "# pip 저장소 설정" \
    && mkdir -p ~/.pip \
    && { \
		echo "[global]"; \
		echo "timeout = 60"; \
		echo "index-url = ${PIP_MIRROR}"; \
		echo "trusted-host = ${PIP_TRUST_HOST}"; \
	} > ~/.pip/pip.conf \
    \
    && echo && echo "# 기본 유틸 설치" \
    && pip3 install --upgrade --no-cache-dir --force-reinstall \
        pip \
        cython \
        setuptools \
        wheel \
    && rm -rf /tmp/*

ARG PIP_OPT='--upgrade --no-cache-dir'
ARG PYTORCH_URL="https://download.pytorch.org/whl/torch_stable.html"

RUN echo && echo "# preinstall" \
    && pip3 install ${PIP_OPT} \
        pip \
        pytest-runner \
        setuptools \
        wheel \
    && rm -rf /tmp/*

RUN echo && echo "# base 설치" \
    && pip3 install ${PIP_OPT} \
		h5py \
		matplotlib \
		pydot \
		smart-open \
        bilm \
        bokeh \
        dask[complete] \
        lxml \
        networkx \
        pyLDAvis \
        tqdm \
        wikiextractor \
        wordcloud \
        xlrd \
        xlsxwriter \
        seaborn \
    && rm -rf /tmp/*

RUN echo && echo "# ML 설치" \
    && pip3 install ${PIP_OPT} \
        soynlp \
        soyspacing \
		numpy \
		pandas \
		scikit-learn \
		sklearn \
        bs4 \
        gensim \
        konlpy \
        nltk \
		scipy \
   && rm -rf /tmp/*

RUN echo && echo "# DL 설치" \
    && pip3 install ${PIP_OPT} \
        bert \
        keras \
        sentencepiece \
        tensorflow \
        tensorflow-hub \
        tf_sentencepiece \
        tfx \
        transformers==2.11.0 \
    && rm -rf /tmp/*

RUN echo && echo "# jupyter 설치" \
    && pip3 install ${PIP_OPT} \
		autopep8 \
		bash_kernel \
		ipykernel \
		ipyparallel \
		jupyter \
		jupyterhub \
		jupyterlab \
		notebook \
		yapf \
		jupyter_contrib_nbextensions \
		jupyter_nbextensions_configurator \
		jupyterthemes \
        PyJWT \
        beakerx \
        py4j \
        qgrid \
        sshkernel \
    && rm -rf /tmp/*

RUN echo && echo "# pytorch 설치" \
    && pip3 install ${PIP_OPT} --find-links ${PYTORCH_URL} \
        torch==1.6.0+cu101 \
        torchtext \
        torchvision==0.7.0+cu101 \
    && rm -rf /tmp/*
