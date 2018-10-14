FROM frolvlad/alpine-python3
RUN apk update
RUN apk add expat-dev python3-dev boost-dev zlib-dev bzip2-dev g++ boost-python3
RUN pip install osmium

WORKDIR /build
COPY osmtogtfs /build/osmtogtfs/
COPY setup.py README.md /build/
RUN python3 setup.py install
RUN find /usr/lib/ -name libboost_* -not -name libboost_python* -delete
RUN find /usr/lib/python3.6 -type f -name "*.pyc" -delete
RUN find /usr/lib/ -name "__pycache__" -type d -delete

FROM frolvlad/alpine-python3
COPY --from=0 /usr/lib/libboost_python3.so* \
              /usr/lib/libstdc++.so* \
              /usr/lib/libgcc_s.so* \
              /usr/lib/
COPY --from=0 /usr/lib/python3.6/site-packages/ /usr/lib/python3.6/site-packages/
COPY --from=0 /usr/bin/o2g /usr/bin/o2g

RUN pip --no-cache-dir install --no-compile flask validators requests

ENV LC_ALL=C.UTF-8
WORKDIR /app
COPY demo/app.py .
COPY demo/templates /app/templates
CMD ["python", "app.py"]
EXPOSE 3000


