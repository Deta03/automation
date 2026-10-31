FROM jenkins/ssh-agent

USER root

RUN apt-get update && apt-get install -y php-cli \
    && rm -rf /var/lib/apt/lists/*
