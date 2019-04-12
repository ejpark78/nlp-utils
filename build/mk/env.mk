
CRAWLER_OPT =
CRAWLER_IMAGE = corpus:5000/crawler:latest

CORPUS_PROCESSOR_IMAGE = corpus:5000/api-center/corpus_processor:latest

RESTART = always

RABBITMQ_USER = user
RABBITMQ_PASS = nlplab!

USE_POST_MQ = 1

# 10lan
ELASTIC_HOST = elasticsearch:10.242.94.49

HTTP_PROXY = http_proxy=http://proxylive.blue.ncsoft:8080
HTTPS_PROXY = https_proxy=http://proxylive.blue.ncsoft:8080

# 업무망
ELASTIC_HOST = elasticsearch:172.20.79.241

HTTP_PROXY = http_proxy=
HTTPS_PROXY = https_proxy=

# etc
COMPOSE_HOST = "-H unix:///var/run/docker.sock"
