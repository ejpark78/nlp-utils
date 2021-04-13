ARG BASE_IMAGE=x11:xfce4
FROM ${BASE_IMAGE}

LABEL maintainer="ejpark@ncsoft.co.kr"

ENV DEBIAN_FRONTEND=noninteractive
ENV HOME=/root LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV NOTVISIBLE "in users profile"

ARG APT_CODE_NAME=focal
ARG APT_MIRROR=http://mirror.kakao.com/ubuntu
ARG PIP_TRUST_HOST=mirror.kakao.com
ARG PIP_MIRROR=http://mirror.kakao.com/pypi/simple

ENV APT_OPTS="--no-install-suggests --no-install-recommends"
ENV PYTHONWARNINGS "ignore:Unverified HTTPS request"

USER root
WORKDIR $HOME

RUN echo && echo "# docker/kubectl 설치" \
    && apt update -yq ${APT_OPTS} \
    && apt install -yq ${APT_OPTS} \
        kubectl \
        docker-ce-cli \
        python3-pip \
        python3-venv \
    \
    && echo && echo "# oh my zsh 설치" \
    && wget "https://github.com/robbyrussell/oh-my-zsh/raw/master/tools/install.sh" -O - | zsh || true \
    && cat ${HOME}/.oh-my-zsh/templates/zshrc.zsh-template | tee ${HOME}/.zshrc \
    && rm -rf ~/.oh-my-zsh/.git \
    \
    && echo && echo "# oh my zsh plugin 설치" \
    && git clone --depth=1 "https://github.com/jonmosco/kube-ps1" ~/.kube-ps1 \
    && git clone --depth=1 "https://github.com/zsh-users/zsh-completions.git" ~/.oh-my-zsh/plugins/zsh-completions \
    && git clone --depth=1 "https://github.com/zsh-users/zsh-syntax-highlighting.git" ~/.oh-my-zsh/plugins/zsh-syntax-highlighting \
    && git clone --depth=1 "https://github.com/zsh-users/zsh-autosuggestions.git" ~/.oh-my-zsh/plugins/zsh-autosuggestions \
    && find ~ -name .git -type d -exec rm -rf {} + \
    \
    && echo && echo "# 저장소 정리" \
    && apt autoremove -yq \
    && rm -rf /var/cache/* /var/lib/apt/lists/* /tmp/* /var/tmp/*

ARG K9S_VER="v0.24.7"
ARG HELM_VER="v3.5.2"
ARG STERN_VER="1.11.0"

RUN echo && echo "# helm 설치" \
	&& wget -O /tmp/helm.tar.gz "https://get.helm.sh/helm-${HELM_VER}-linux-amd64.tar.gz" \
    && tar xvfz /tmp/helm.tar.gz -C /tmp \
    && mv /tmp/linux-amd64/helm /usr/bin/ \
    \
    && echo && echo "# k9s 설치" \
    && wget -O /tmp/k9s.tar.gz "https://github.com/derailed/k9s/releases/download/${K9S_VER}/k9s_Linux_x86_64.tar.gz" \
    && tar xvfz /tmp/k9s.tar.gz -C /tmp \
    && mv /tmp/k9s /usr/bin/ \
    \
    && echo && echo "# stern 설치" \
    && wget -O /usr/bin/stern "https://github.com/wercker/stern/releases/download/${STERN_VER}/stern_linux_amd64" \
    && chmod +x /usr/bin/stern \
    \
    && echo && echo "# krew 설치" \
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
    && mv /root/.krew /home/ubuntu/.krew \
    && chown -R ubuntu:ubuntu /home/ubuntu \
    && rm -rf /var/cache/* /var/lib/apt/lists/* /tmp/* /var/tmp/*

#ADD zshrc .zshrc
ADD docker-config.json .docker/config.json

EXPOSE 3389 9001

CMD ["supervisord"]
