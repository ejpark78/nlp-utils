FROM ubuntu:20.04

LABEL maintainer="ejpark@ncsoft.co.kr"

ENV DEBIAN_FRONTEND=noninteractive
ENV HOME=/root LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV NOTVISIBLE "in users profile"

ARG APT_CODE_NAME=focal
ARG APT_MIRROR=http://mirror.kakao.com/ubuntu
ARG PIP_TRUST_HOST=mirror.kakao.com
ARG PIP_MIRROR=http://mirror.kakao.com/pypi/simple

ENV APT_OPTS="--no-install-suggests --no-install-recommends"

USER root
WORKDIR $HOME

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
		bash \
        apt-transport-https \
        ca-certificates \
        curl \
        git \
        gnupg \
        gpg-agent \
        openssh-client \
        software-properties-common \
        tmux \
        vim \
        wget \
        zsh \
    && echo && echo "# docker/kubectl 설치" \
	&& curl -s "https://packages.cloud.google.com/apt/doc/apt-key.gpg" | apt-key add - \
	&& curl -fsSL "https://download.docker.com/linux/ubuntu/gpg" | apt-key add - \
    && apt-add-repository "deb http://apt.kubernetes.io/ kubernetes-xenial main" \
    && apt-add-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu ${APT_CODE_NAME} stable" \
    && apt update -yq ${APT_OPTS} \
    && apt install -yq ${APT_OPTS} \
        kubectl \
        docker-ce-cli \
    && echo && echo "# oh my zsh 설치" \
    && wget https://github.com/robbyrussell/oh-my-zsh/raw/master/tools/install.sh -O - | zsh || true \
    && cat ${HOME}/.oh-my-zsh/templates/zshrc.zsh-template | tee ${HOME}/.zshrc \
    && rm -rf ~/.oh-my-zsh/.git \
    && echo && echo "# oh my zsh plugin 설치" \
    && git clone --depth=1 https://github.com/jonmosco/kube-ps1 ~/.kube-ps1 \
    && git clone --depth=1 https://github.com/zsh-users/zsh-completions.git ~/.oh-my-zsh/plugins/zsh-completions \
    && git clone --depth=1 https://github.com/zsh-users/zsh-syntax-highlighting.git ~/.oh-my-zsh/plugins/zsh-syntax-highlighting \
    && git clone --depth=1 https://github.com/zsh-users/zsh-autosuggestions.git ~/.oh-my-zsh/plugins/zsh-autosuggestions \
    && find ~ -name .git -type d -exec rm -rf {} + \
    && echo && echo "# build library 삭제" \
    && apt purge -yq \
        software-properties-common \
    && apt autoremove -yq \
    && rm -rf /var/cache/* /var/lib/apt/lists/* /tmp/* /var/tmp/*

ARG HELM_VER="v3.5.2"
ARG K9S_VER="v0.24.6"
ARG STERN_VER="1.11.0"

RUN echo && echo "# helm 설치" \
	&& wget -O /tmp/helm.tar.gz "https://get.helm.sh/helm-${HELM_VER}-linux-amd64.tar.gz" \
    && tar xvfz /tmp/helm.tar.gz -C /tmp \
    && mv /tmp/linux-amd64/helm /usr/bin/ \
    && echo && echo "# k9s 설치" \
    && wget -O /tmp/k9s.tar.gz "https://github.com/derailed/k9s/releases/download/${K9S_VER}/k9s_Linux_x86_64.tar.gz" \
    && tar xvfz /tmp/k9s.tar.gz -C /tmp \
    && mv /tmp/k9s /usr/bin/ \
    && echo && echo "# stern 설치" \
    && wget -O /usr/bin/stern "https://github.com/wercker/stern/releases/download/${STERN_VER}/stern_linux_amd64" \
    && chmod +x /usr/bin/stern \
    && rm -rf /var/cache/* /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN echo && echo "# krew 설치" \
    && wget -O /tmp/krew.tar.gz "https://github.com/kubernetes-sigs/krew/releases/latest/download/krew.tar.gz" \
    && tar zxvf /tmp/krew.tar.gz -C /tmp \
    && mv /tmp/krew-linux_amd64 /usr/bin/krew \
    && chmod +x /usr/bin/krew \
    && krew install krew \
    && export PATH="${KREW_ROOT:-$HOME/.krew}/bin:$PATH" \
    && kubectl krew update \
    && kubectl krew install ctx \
    && kubectl krew install ns \
    && kubectl krew install konfig \
    && rm -rf /var/cache/* /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN echo && echo "# ttyd 설치" \
    && apt update -yq ${APT_OPTS} \
    && apt install -yq ${APT_OPTS} \
        build-essential \
        cmake \
        git \
        libjson-c-dev \
        libwebsockets-dev \
    && cd /tmp/ \
    && git clone "https://github.com/tsl0922/ttyd.git" \
    && cd ttyd \
    && mkdir build \
    && cd build \
    && cmake .. \
    && make \
    && make install \
    && echo && echo "# build library 삭제" \
    && apt purge -yq \
        build-essential \
        cmake \
    && apt autoremove -yq \
    && rm -rf /var/cache/* /var/lib/apt/lists/* /tmp/* /var/tmp/*

#RUN echo && echo "# ssh kubeconfig 설치" \
#    && git clone --depth=1 http://ejpark:z5qdkW9xda4YGyUsa6jQ@galadriel02.korea.ncsoft.corp/ejpark/ssh ~/.ssh \
#    && git clone --depth=1 http://ejpark:-_VTvKxdyZjG37C-U9px@galadriel02.korea.ncsoft.corp/ejpark/kubeconfig ~/.kube \
#    && echo && echo "# merge kubeconfig" \
#    && cd ~/.kube/cluster.d \
#    && KUBECONFIG=nc-crawler:nc-od:nc-utils:nc-web:nlp kubectl config view --merge --flatten > ~/.kube/config \
#    && rm -rf ~/.kube/cluster.d \
#    && find ~ -name .git -type d -exec rm -rf {} + \
#    && chmod 600 ~/.ssh && chmod -R 400 ~/.ssh/*

ADD zshrc .zshrc
ADD ssh-config .ssh/config
ADD docker-config.json .docker/config.json
ADD docker-daemon.json /etc/docker/daemon.json

ENV PORT=80
ENV USER_AUTH=admin:searchT2020

CMD ["ttyd", "--port", "${PORT}", "--credential", "${USER_AUTH}", "zsh"]

#  && adduser --quiet --disabled-password --shell /bin/zsh --home /home/$USER_NAME --gecos "User" $USER_NAME
#  && echo "${USER_NAME}:${USER_PASSWORD}" | chpasswd && usermod -aG sudo $USER_NAME

# other web tty: https://github.com/butlerx/wetty
# Wetty: Node based web terminal (SSH/login): https://github.com/butlerx/wetty
# GoTTY: Go based web terminal: https://github.com/yudai/gotty
