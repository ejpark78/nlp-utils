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
    && apt update -yq ${APT_OPTS} \
    && apt install -yq ${APT_OPTS} \
        apt-transport-https \
        build-essential \
        bzip2 \
        ca-certificates \
        cmake \
        curl \
        dos2unix \
        fontconfig \
        git \
        gzip \
        htop \
        jq \
        language-pack-ko \
        libcurl4-openssl-dev \
        libgoogle-perftools-dev \
        libssl-dev \
        libxml2-dev \
        libxslt-dev \
        locales \
        net-tools \
        openjdk-8-jdk \
        p7zip \
        parallel \
        pbzip2 \
        pkg-config \
        python3 \
        python3-dev \
        python3-pip \
        python3-pycurl \
        sqlite3 \
        sudo \
        texlive-base \
        tmux \
        tzdata \
        unzip \
        vim \
        wget \
        zip \
        zsh \
    && echo && echo "# 폰트 초기화 & 한글 폰트 설치" \
    && apt install -yq ${APT_OPTS} \
        fonts-baekmuk \
        fonts-nanum* \
        fonts-unfonts-core \
        fonts-unfonts-extra \
    && rm -rf /usr/share/fonts/truetype/dejavu \
    && fc-cache -f -v \
    && fmtutil-sys --all \
    && echo && echo "# oh my zsh 설치" \
    && wget https://github.com/robbyrussell/oh-my-zsh/raw/master/tools/install.sh -O - | zsh || true \
    && cat ${HOME}/.oh-my-zsh/templates/zshrc.zsh-template | tee ${HOME}/.zshrc \
    && echo && echo "# 저장소 정리" \
    && rm -rf /var/cache/* /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN echo && echo "nodejs 설치" \
    && curl -sL https://deb.nodesource.com/setup_12.x | bash - \
    && apt update -yq ${APT_OPTS} \
    && apt install -yq ${APT_OPTS} \
        nodejs \
    && echo && echo "# 저장소 정리" \
    && rm -rf /var/cache/* /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN echo && echo "# locale-gen" \
    && { \
		echo "en_US.UTF-8 UTF-8"; \
		echo "ko_KR.UTF-8 UTF-8"; \
		echo "ko_KR.EUC-KR EUC-KR"; \
	} >> /etc/locale.gen \
    && locale-gen \
    && locale-gen ko_KR.UTF-8 \
    && update-locale LANG=ko_KR.UTF-8 \
    && dpkg-reconfigure locales \
    \
    && echo && echo "# timezone 설정" \
    && ln -fs /usr/share/zoneinfo/Asia/Seoul /etc/localtime \
    && dpkg-reconfigure --frontend noninteractive tzdata

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
    && echo && echo "# jupyter 설치" \
    && pip3 install --upgrade --no-cache-dir \
		autopep8 \
		bash_kernel \
        jupyter \
        jupyterlab \
        jupyterthemes \
        jupyter_contrib_nbextensions \
        qgrid \
        sshkernel \
    && echo && echo "jupyter kernel 설치" \
    && python3 -m sshkernel install \
    && python3 -m bash_kernel.install \
	\
    && echo && echo "nbextension enable 설정" \
    && jupyter contrib nbextension install \
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

ARG MINIO_URI=http://172.19.168.48:9000
ARG MINIO_ACCESS_KEY="minio"
ARG MINIO_SECRET_KEY="minio123"
ARG MINIO_BUCKET="cache"
ARG MINIO_PATH="build"

RUN echo && echo "minio client" \
	&& wget https://dl.min.io/client/mc/release/linux-amd64/mc \
	&& chmod +x mc \
	&& mv mc /usr/bin/ \
	&& mc alias set ${MINIO_BUCKET} ${MINIO_URI} ${MINIO_ACCESS_KEY} ${MINIO_SECRET_KEY}

ENV BUILD_HOME=/usr/local

# sentencepiece 설치
RUN echo && echo "# sentencepiece 설치" \
    && mc cp ${MINIO_BUCKET}/${MINIO_PATH}/sentencepiece.tar.gz ${BUILD_HOME}/sentencepiece.tar.gz \
    && tar xvfz ${BUILD_HOME}/sentencepiece.tar.gz -C ${BUILD_HOME}\
    && cd ${BUILD_HOME}/sentencepiece/build \
    && make install \
    && ldconfig -v \
    && rm -rf /tmp/* ${BUILD_HOME}/sentencepiece ${BUILD_HOME}/sentencepiece.tar.gz

# konlpy/mecab 설치
RUN echo && echo "# konlpy/mecab 설치" \
    && mc cp ${MINIO_BUCKET}/${MINIO_PATH}/mecab.tar.gz ${BUILD_HOME}/mecab.tar.gz \
    && tar xvfz ${BUILD_HOME}/mecab.tar.gz -C ${BUILD_HOME} \
    && cd ${BUILD_HOME}/mecab \
    && make check \
    && make install \
    && rm -rf ${BUILD_HOME}/mecab ${BUILD_HOME}/mecab.tar.gz \
    \
    && mc cp ${MINIO_BUCKET}/${MINIO_PATH}/mecab-ko-dic.tar.gz ${BUILD_HOME}/mecab-ko-dic.tar.gz \
    && tar xvfz ${BUILD_HOME}/mecab-ko-dic.tar.gz -C ${BUILD_HOME} \
    && cd ${BUILD_HOME}/mecab-ko-dic \
    && mecab-config --libs-only-L | $sudo tee /etc/ld.so.conf.d/mecab.conf \
    && ldconfig -v \
    && make -j $(nproc) \
    && echo "dicdir=/usr/local/lib/mecab/dic/mecab-ko-dic" > /usr/local/etc/mecabrc \
    && make install \
    && rm -rf ${BUILD_HOME}/mecab-ko-dic ${BUILD_HOME}/mecab-ko-dic.tar.gz /tmp/* \
    \
    && mc cp ${MINIO_BUCKET}/${MINIO_PATH}/mecab-python.tar.gz ${BUILD_HOME}/mecab-python.tar.gz \
    && tar xvfz ${BUILD_HOME}/mecab-python.tar.gz -C ${BUILD_HOME} \
    && cd ${BUILD_HOME}/mecab-python \
    && pip3 install mecab-python \
    && rm -rf ${BUILD_HOME}/mecab-python ${BUILD_HOME}/mecab-python.tar.gz /tmp/*

# stanfordnlp/glove 설치
RUN echo && echo "# stanfordnlp/glove 설치" \
    && mc cp ${MINIO_BUCKET}/${MINIO_PATH}/glove.tar.gz ${BUILD_HOME}/glove.tar.gz \
    && tar xvfz ${BUILD_HOME}/glove.tar.gz -C ${BUILD_HOME} \
    && rm -rf ${BUILD_HOME}/glove.tar.gz /tmp/*

# facebookresearch/fastText 설치
RUN echo && echo "# facebookresearch/fastText 설치" \
    && mc cp ${MINIO_BUCKET}/${MINIO_PATH}/fastText.tar.gz ${BUILD_HOME}/fastText.tar.gz \
    && tar xvfz ${BUILD_HOME}/fastText.tar.gz -C ${BUILD_HOME} \
    && cd ${BUILD_HOME}/fastText/build \
    && make install \
    && cd .. \
    && pip3 install --upgrade --no-cache-dir . \
    && rm -rf ${BUILD_HOME}/fastText ${BUILD_HOME}/fastText.tar.gz /tmp/*

# kakao/khaiii 설치
RUN echo && echo "# kakao/khaiii 설치" \
    && mc cp ${MINIO_BUCKET}/${MINIO_PATH}/khaiii.tar.gz ${BUILD_HOME}/khaiii.tar.gz \
    && tar xvfz ${BUILD_HOME}/khaiii.tar.gz -C ${BUILD_HOME} \
    && cd ${BUILD_HOME}/khaiii/build \
    && make resource \
    && make large_resource \
    && make install \
    \
    && cd package_python \
    && pip3 install . \
    \
    && rm -rf ${BUILD_HOME}/khaiii ${HOME}/.hunter ${BUILD_HOME}/khaiii.tar.gz /tmp/*

RUN echo && echo "oh my zsh 설정" \
    && sed -i -r 's/^plugins=\(/plugins=\(kubectl kube-ps1 /' ${HOME}/.zshrc \
    && echo "if [ /usr/bin/kubectl ]; then source <(kubectl completion zsh); fi" >> ${HOME}/.zshrc
    
RUN echo && echo "kubernetes utils: k9s" \
    && wget https://github.com/derailed/k9s/releases/download/v0.24.2/k9s_Linux_x86_64.tar.gz \
    && tar xvfz k9s_Linux_x86_64.tar.gz -C /tmp \
    && mv /tmp/k9s /usr/bin/ \
    && rm k9s_Linux_x86_64.tar.gz /tmp/* 

RUN echo && echo "kubernetes utils: helm" \
    && wget https://get.helm.sh/helm-v3.4.2-linux-amd64.tar.gz \
    && tar xvfz helm-v3.4.2-linux-amd64.tar.gz -C /tmp \
    && sudo mv /tmp/linux-amd64/helm /usr/bin/ \
    && rm -rf helm-v3.4.2-linux-amd64.tar.gz /tmp/*

WORKDIR /home/jovyan

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
