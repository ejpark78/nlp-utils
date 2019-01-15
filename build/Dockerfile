FROM base/crawler:latest

LABEL maintainer="ejpark@ncsoft.co.kr"

ENV UID=1000 GID=1000 USER=crawler

RUN echo "사용자 생성: ${USER}..." \
    && mkdir -p ${APP_HOME} \
	&& echo "사용자 생성..." \
	&& addgroup --gid ${GID} ${USER} \
	&& useradd --no-create-home --uid ${UID} --gid ${GID} -s /bin/bash ${USER} \
	&& chown -R ${UID}:${GID} ${APP_HOME} \
	&& usermod -G sudo ${USER} \
	&& echo "${USER} ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

ADD app.tar.gz ${APP_HOME}

RUN pip3 install --no-cache-dir -r /usr/local/app/requirements.txt
RUN pip3 install --no-cache-dir -U requests[security]

WORKDIR ${APP_HOME}
