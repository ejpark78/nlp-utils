ARG BASE_IMAGE=tensorflow/tensorflow:2.0.0-py3

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

RUN echo && echo "# APT MIRROR 변경: ${APT_MIRROR}" \
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
        apt-transport-https \
        bash \
        build-essential \
        bzip2 \
        ca-certificates \
        curl \
        emacs \
        g++ \
        git \
        gnupg \
        graphviz \
        kubectl=1.15.12-00 \
        locales \
        lsb-release \
        openssh-client \
        python3-dev \
        python3-pip \
        python3-setuptools \
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
    && pip3 install --upgrade --no-cache-dir \
        cython \
        cmake \
        pip \
        pytest-runner \
        setuptools \
        wheel \
    && pip3 install --upgrade --no-cache-dir \
        dill \
        kfp \
        kfserving \
        kubeflow-fairing \
        kubeflow-kale \
        msrestazure \
        keras \
        konlpy \
        qgrid \
        six \
        cloudpickle==1.1.1 \
    && pip3 install --upgrade --no-cache-dir \
        jupyter \
        jupyterlab \
		autopep8 \
		bash_kernel \
        sshkernel \
    && echo && echo "jupyter kernel 설치" \
    && python3 -m sshkernel install \
    && python3 -m bash_kernel.install \
    && echo && echo "nbextension enable 설정" \
    && jupyter labextension install qgrid \
	&& jupyter labextension install ipyvolume \
    && jupyter labextension install @jupyter-widgets/jupyterlab-manager \
	\
	&& echo && echo "nbextension enable 설정" \
	&& jupyter nbextension enable --py --sys-prefix qgrid \
    && jupyter nbextension enable --py --sys-prefix widgetsnbextension \
	\
    && rm -rf /tmp/* \
    && jupyter serverextension enable --py jupyterlab --sys-prefix

RUN echo && echo "oh my zsh 설치" \
    && curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh | bash - \
    && cat ${HOME}/.oh-my-zsh/templates/zshrc.zsh-template | tee ${HOME}/.zshrc \
    && sed -i -r 's/^plugins=\(/plugins=\(kubectl kube-ps1 /' ${HOME}/.zshrc \
    && echo "if [ /usr/bin/kubectl ]; then source <(kubectl completion zsh); fi" >> ${HOME}/.zshrc \
    \
    && echo && echo "kubernetes utils: k9s" \
    && wget https://github.com/derailed/k9s/releases/download/v0.22.1/k9s_Linux_x86_64.tar.gz \
    && tar xvfz k9s_Linux_x86_64.tar.gz -C /tmp \
    && mv /tmp/k9s /usr/bin/ \
    && rm k9s_Linux_x86_64.tar.gz /tmp/* \
    \
	&& echo && echo "kubernetes utils: krew" \
    && curl -fsSLO "https://github.com/kubernetes-sigs/krew/releases/latest/download/krew.tar.gz" \
    && tar zxvf krew.tar.gz -C /tmp \
    && mv /tmp/krew-linux_amd64 /usr/bin/krew \
    && rm krew.tar.gz /tmp/* \
    && chmod +x /usr/bin/krew \
    && krew install krew \
    && export PATH="${HOME}/.krew/bin:$PATH" \
    && kubectl krew update \
    && kubectl krew install ctx \
    && kubectl krew install ns \
    \
	&& echo && echo "kubeflow utils: minio client" \
	&& wget https://dl.min.io/client/mc/release/linux-amd64/mc \
	&& chmod +x mc \
	&& mv mc /usr/bin/

#	 mc alias set minio http://minio-service.kubeflow.svc.cluster.local:9000 minio minio123

WORKDIR /home/jovyan

ARG NB_USER=jovyan

EXPOSE 8888

ENV NB_USER $NB_USER
ENV NB_UID=1000
ENV NB_PREFIX /
#ENV HOME /home/$NB_USER

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
        --NotebookApp.terminado_settings=\"{'shell_command': ['/usr/bin/zsh']}\"\
"]
