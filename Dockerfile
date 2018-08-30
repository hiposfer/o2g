FROM ubuntu:bionic

ENV LC_ALL=C.UTF-8
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app
COPY . /app

RUN \
  apt-get update && \
  apt-get install --yes python3-pyosmium python3-pip && \
  pip3 install -I pyopenssl && \
  pip3 install -r requirements.txt && \
  pip3 install flask validators requests && \
  python3 setup.py install && \
  apt-get remove --yes python3-pip && \
  apt-get install --yes python3-setuptools python3-six && \
  apt-get autoremove --yes --purge && \
  rm -rf /var/lib/apt/lists/* && \
  rm -rf /app

COPY demo /app
CMD ["python3", "app.py"]
EXPOSE 3000
