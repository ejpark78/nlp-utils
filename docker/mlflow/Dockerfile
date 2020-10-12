ARG BASE_IMAGE=tensorflow/tensorflow:2.3.0

FROM ${BASE_IMAGE}

LABEL author="박은진<ejpark78@gmail.com>"

ENV DEBIAN_FRONTEND=noninteractive
ENV HOME=/root LANG=C.UTF-8 LC_ALL=C.UTF-8 LANGUAGE=ko_KR:en

ARG APT_CODE_NAME=bionic
ARG APT_MIRROR=http://mirror.kakao.com/ubuntu
ARG PIP_MIRROR=http://mirror.kakao.com/pypi/simple
ARG PIP_TRUST_HOST=mirror.kakao.com

ENV APT_OPTS="--no-install-suggests --no-install-recommends"
ENV PYTHONWARNINGS="ignore:Unverified HTTPS request"

USER root

RUN echo && echo "# BASE_IMAGE: ${BASE_IMAGE}" \
    && echo && echo "# APT MIRROR 변경: ${APT_MIRROR}" \
	&& { \
		echo "Acquire::https {"; \
		echo "  Verify-Peer false;"; \
		echo "  Verify-Host false;"; \
		echo "};"; \
	} > /etc/apt/apt.conf.d/mirror.conf \
    \
	&& { \
		echo "deb ${APT_MIRROR} ${APT_CODE_NAME} main restricted universe multiverse"; \
		echo "deb ${APT_MIRROR} ${APT_CODE_NAME}-updates main restricted universe multiverse"; \
		echo "deb ${APT_MIRROR} ${APT_CODE_NAME}-backports main restricted universe multiverse"; \
	} > /etc/apt/sources.list \
    \
    && curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add - \
    && echo "deb https://apt.kubernetes.io/ kubernetes-xenial main" | tee -a /etc/apt/sources.list.d/kubernetes.list \
    && apt update -yq ${APT_OPTS} \
    && apt install -yq ${APT_OPTS} \
        bash \
        bzip2 \
        curl \
        g++ \
        git \
        unzip \
        vim \
        wget \
        zip \
        zsh \
    && echo && echo "nodejs 설치" \
    && curl -sL https://deb.nodesource.com/setup_12.x | bash - \
    && apt update -yq ${APT_OPTS} \
    && apt install -yq ${APT_OPTS} \
        nodejs \
    && echo && echo "# 저장소 정리" \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV PATH /usr/local/conda/bin:$PATH

RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh \
    && /bin/bash /tmp/miniconda.sh -b -p /usr/local/conda \
    && rm /tmp/miniconda.sh \
    && ln -s /usr/local/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh \
    && echo ". /usr/local/conda/etc/profile.d/conda.sh" >> ~/.zshrc \
    && echo "conda activate base" >> ~/.zshrc

RUN conda update conda \
    && rm $HOME/.pip/pip.conf

RUN echo && echo "# mlflow 설치" \
    && pip3 install --upgrade --no-cache-dir \
        mlflow \
        sklearn \
        matplotlib \
        keras \
        konlpy \
        qgrid \
        six \
    && pip3 install --upgrade --no-cache-dir \
        psycopg2-binary \
    && pip3 install --upgrade --no-cache-dir \
        jupyter \
        jupyterlab \
        jupyterthemes \
		autopep8 \
		bash_kernel \
        sshkernel \
	\
    && echo && echo "jupyter kernel 설치" \
    && python3 -m sshkernel install \
    && python3 -m bash_kernel.install \
	\
    && echo && echo "nbextension enable 설정" \
    && jupyter labextension install qgrid \
	&& jupyter labextension install ipyvolume \
    && jupyter labextension install @jupyter-widgets/jupyterlab-manager \
	\
	&& echo && echo "nbextension enable 설정" \
	&& jupyter nbextension enable --py --sys-prefix qgrid \
    && jupyter nbextension enable --py --sys-prefix widgetsnbextension \
	\
    && jupyter serverextension enable --py jupyterlab --sys-prefix \
	\
	&& echo && echo "jupyter notebook 테마 설정" \
	&& jt -t monokai -fs 11 -tfs 11 -nfs 11 -ofs 11 -cellw 980 -T -f hack -N -cellw 1280 -lineh 150 \
    && rm -rf /tmp/*

RUN echo && echo "# DL 설치" \
    && pip3 install --upgrade --no-cache-dir \
        bert \
        keras \
        tensorflow-hub \
        tf_sentencepiece \
        tfx \
    && rm -rf /tmp/*

ARG PYTORCH_URL="https://download.pytorch.org/whl/torch_stable.html"
RUN echo && echo "# torch 설치" \
    && pip3 install --upgrade --no-cache-dir --find-links ${PYTORCH_URL} \
        torch==1.6.0+cu101 \
        torchtext \
        torchvision==0.7.0+cu101 \
    && rm -rf /tmp/*

RUN echo && echo "# transformers 설치" \
    && pip3 install --upgrade --no-cache-dir \
        transformers==2.11.0 \
    && rm -rf /tmp/*

RUN echo && echo "oh my zsh 설치" \
    && curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh | bash - \
    && cat ${HOME}/.oh-my-zsh/templates/zshrc.zsh-template | tee ${HOME}/.zshrc

ARG MINIO_URI="http://minio-service.kubeflow.svc.cluster.local:9000"
ARG MINIO_ACCESS_KEY="minio"
ARG MINIO_SECRET_KEY="minio123"
ARG MINIO_BUCKET="minio"

RUN echo && echo "minio alias" \
	&& { \
		echo "("; \
		echo "sleep 60;"; \
		echo "mc alias set ${MINIO_BUCKET} ${MINIO_URI} ${MINIO_ACCESS_KEY} ${MINIO_SECRET_KEY}"; \
		echo ") &"; \
	} > /usr/bin/minio_alias.sh \
    && chmod +x /usr/bin/minio_alias.sh

WORKDIR /home/jovyan

ARG NB_USER=jovyan

EXPOSE 8888

ENV NB_USER $NB_USER
ENV NB_UID=1000
ENV NB_PREFIX /
#ENV HOME /home/$NB_USER

CMD ["bash", "-c", "\
    /usr/bin/minio_alias.sh ;\
    jupyter lab \
        --no-browser \
        --ip=0.0.0.0 \
        --port=8888 \
        --allow-root \
        --LabApp.token='' \
        --LabApp.password='' \
        --LabApp.allow_origin='*' \
        --LabApp.base_url=${NB_PREFIX} \
        --notebook-dir=/home/jovyan \
        --NotebookApp.iopub_data_rate_limit=10000000 \
        --NotebookApp.terminado_settings=\"{'shell_command': ['/usr/bin/zsh']}\"\
"]

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
