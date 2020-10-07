ARG BASE_IMAGE=registry/dev/embedding:base

FROM ${BASE_IMAGE}

LABEL author="박은진<ejpark78@gmail.com>"

ENV DEBIAN_FRONTEND=noninteractive
ENV HOME=/root LANG=C.UTF-8 LC_ALL=C.UTF-8 LANGUAGE=ko_KR:en

ARG APT_CODE_NAME=bionic
ARG APT_MIRROR=http://mirror.kakao.com/ubuntu
ARG PIP_MIRROR=http://mirror.kakao.com/pypi/simple
ARG PIP_TRUST_HOST=mirror.kakao.com

USER root

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
		cython \
        cmake \
        pip \
        pytest-runner \
        setuptools \
        wheel \
    && rm -rf /tmp/*

RUN echo && echo "# ML 설치" \
    && pip3 install --upgrade --no-cache-dir \
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
        seaborn \
        soynlp \
        soyspacing \
        tqdm \
        wikiextractor \
        wordcloud \
        xlrd \
        xlsxwriter \
    && pip3 install --upgrade --no-cache-dir \
		numpy \
		pandas \
		scikit-learn \
		scipy \
		sklearn \
        gensim \
        konlpy \
        nltk \
    && rm -rf /tmp/*

RUN echo && echo "# DL 설치" \
    && pip3 install --upgrade --no-cache-dir \
        bert \
        keras \
        sentencepiece \
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

RUN echo && echo "# jupyter 설치" \
	&& pip3 install --upgrade --no-cache-dir \
		autopep8 \
		jupyter \
		jupyterlab \
		notebook \
		yapf \
	&& pip3 install --upgrade --no-cache-dir \
		jupyter_contrib_nbextensions \
		jupyter_nbextensions_configurator \
		jupyterthemes \
        PyJWT \
        beakerx \
        py4j \
        qgrid \
		bash_kernel \
        sshkernel \
    && mkdir -p ${HOME}/.jupyter \
    \
    && echo && echo "jupyter plugin 설치" \
    && python3 -m sshkernel install \
    && python3 -m bash_kernel.install \
    \
    && echo && echo "nbextension 설치" \
	&& jupyter contrib nbextension install \
    && jupyter nbextension install --sys-prefix --py ipyparallel \
    && jupyter nbextension enable ipyparallel --py --sys-prefix \
	&& jupyter nbextensions_configurator enable \
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
	&& echo && echo "jupyter notebook 테마 설정" \
	&& jt -t monokai -fs 11 -tfs 11 -nfs 11 -ofs 11 -cellw 980 -T -f hack -N -cellw 1280 -lineh 150 \
    && rm -rf /tmp/*

ARG USER=user
ARG UID=1000
ARG GID=1000

ENV USER=${USER} HOME=/home/${USER}

# skel & entrypoint 설치
COPY skel.tar.gz ${HOME}/skel.tar.gz
COPY entrypoint.sh ${HOME}/entrypoint.sh

RUN mkdir -p ${HOME}/.local/bin \
    && cd ${HOME} \
    && tar xvfz skel.tar.gz \
    && rm -rf skel.tar.gz \
    && chown -R ${UID}:${GID} ${HOME} \
    && usermod -d ${HOME} ${USER} \
    && chmod +x ${HOME}/entrypoint.sh

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

RUN mkdir -p /home/jovyan

USER root
WORKDIR /home/jovyan

ENV NB_PREFIX /

CMD ["bash", "-c", "\
    jupyter lab \
        --no-browser \
        --ip=0.0.0.0 \
        --port=8888 \
        --allow-root \
        --notebook-dir=/home/jovyan \
        --LabApp.token='' \
        --LabApp.password='' \
        --LabApp.allow_origin='*' \
        --LabApp.base_url=${NB_PREFIX} \
        --NotebookApp.iopub_data_rate_limit=10000000 \
        --NotebookApp.terminado_settings=\"{'shell_command': ['/bin/zsh']}\"\
"]
