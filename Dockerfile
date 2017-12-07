FROM ubuntu:bionic

ENV LC_ALL=C.UTF-8
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app
COPY . /app

RUN \
  apt-get update && \
  apt-get install --yes python3-pyosmium python3-pip && \
  pip3 install -r requirements.txt && \
  python3 setup.py install && \
  apt-get remove --yes python3-pip && \
  apt-get install --yes python3-setuptools && \
  apt-get autoremove --yes --purge && \
  rm -rf /var/lib/apt/lists/* && \
  rm -rf /app


ENTRYPOINT ["osmtogtfs", "--outdir", "/data"]
