FROM python:3.12.8-alpine AS build
WORKDIR /build
RUN apk add --no-cache openjdk11-jre-headless
RUN pip install requests
COPY *.py ./

ARG MRPACK_FILE
ARG MRPACK_VERSION
ARG MRPACK_ID
ARG INSTALL_OPTIONAL_MODS=1
ENV INSTALL_OPTIONAL_MODS=${INSTALL_OPTIONAL_MODS}

ARG MAX_RAM=4G
ARG MIN_RAM=2G
ARG TYPICAL_START_ARGS="-XX:+UnlockExperimentalVMOptions -XX:+UseG1GC -XX:G1NewSizePercent=20 -XX:G1ReservePercent=20 -XX:MaxGCPauseMillis=50 -XX:G1HeapRegionSize=32M"
ARG ADDITIONAL_START_ARGS
ENV MAX_RAM=${MAX_RAM}
ENV MIN_RAM=${MIN_RAM}
ENV TYPICAL_START_ARGS=${TYPICAL_ADDITIONAL_START_ARGS}
ENV ADDITIONAL_START_ARGS=${ADDITIONAL_START_ARGS}

COPY [ "${MRPACK_FILE}", "modpack.mrpack" ]
RUN python server_downloader.py download ${MRPACK_VERSION} ${MRPACK_ID}
COPY overrides/* server

FROM alpine:3 AS runtime
RUN addgroup -S mcserver && adduser -S mcserver -G mcserver
USER mcserver:mcserver
WORKDIR /server
COPY --from=build --chown=mcserver:mcserver /build/server /server
RUN apk add --no-cache $(cat /server/java-version)

ENTRYPOINT [ "/bin/sh" ]
CMD [ "start.sh" ]
