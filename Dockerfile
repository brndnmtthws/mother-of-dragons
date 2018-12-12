FROM python:3-slim

WORKDIR /usr/src/app

COPY . src
RUN cd src \
  && pip install --no-cache-dir . \
  && cd .. \
  && rm -rf src

ENTRYPOINT [ "mother-of-dragons" ]
