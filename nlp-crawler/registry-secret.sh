SECRET_NAME=registry
USER_ID=k8s
USER_PW=nlplab
USER_EMAIL=ejpark78@gmail.com
REGISTRY_NS=crawler

kubectl create secret docker-registry \
    ${SECRET_NAME} \
    --docker-server=registry.nlp-utils \
    --docker-username=${USER_ID} \
    --docker-password=${USER_PW} \
    --docker-email=${USER_EMAIL} \
    --namespace=${REGISTRY_NS}
