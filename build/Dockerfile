ARG BASE_IMAGE=base/crawler:latest
FROM ${BASE_IMAGE}

LABEL maintainer="ejpark@ncsoft.co.kr"

RUN mkdir -p ${APP_HOME}
ADD app.tar.gz ${APP_HOME}

#RUN pip3 install --no-cache-dir -r /usr/local/app/requirements.txt
#COPY Dockerfile ${APP_HOME}

WORKDIR ${APP_HOME}
