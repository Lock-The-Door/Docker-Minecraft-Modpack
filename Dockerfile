FROM python:3.12.8-alpine AS build
WORKDIR /build
RUN apk add --no-cache openjdk21-jre-headless
RUN pip install requests
COPY *.py ./

ARG MRPACK_FILE
ARG MRPACK_ID
ARG INSTALL_OPTIONAL_MODS=1
ENV INSTALL_OPTIONAL_MODS=${INSTALL_OPTIONAL_MODS}

ARG MAX_RAM=4G
ARG MIN_RAM=2G
ARG TYPICAL_START_ARGS="-XX:+UnlockExperimentalVMOptions -XX:+UseG1GC -XX:G1NewSizePercent=20 -XX:G1ReservePercent=20 -XX:MaxGCPauseMillis=50 -XX:G1HeapRegionSize=32M"
ARG ADDITIONAL_START_ARGS
ENV MAX_RAM=${MAX_RAM}
ENV MIN_RAM=${MIN_RAM}
ENV TYPICAL_START_ARGS=${TYPICAL_START_ARGS}
ENV ADDITIONAL_START_ARGS=${ADDITIONAL_START_ARGS}

COPY [ "${MRPACK_FILE}", "modpack.mrpack" ]
RUN python server_downloader.py mrpack ${MRPACK_ID}
RUN python server_downloader.py mods
RUN python server_downloader.py server


FROM alpine:3 AS runtime
RUN addgroup -S mcserver && adduser -S mcserver -G mcserver
WORKDIR /server
RUN echo "eula=true" > eula.txt
VOLUME [ "/data" ]
RUN mkdir -p /data/world && touch /data/server.properties && touch /data/ops.json && touch /data/whitelist.json && touch /data/banned-ips.json && touch /data/banned-players.json
RUN ln -s /data/world && ln -s /data/server.properties && ln -s /data/ops.json && ln -s /data/whitelist.json && ln -s /data/banned-ips.json && ln -s /data/banned-players.json

COPY --from=build /build/java-version /java-version
RUN apk add --no-cache $(cat /java-version)
RUN rm /java-version

# USER mcserver:mcserver
COPY --from=build /build/server /server
VOLUME [ "/server/config" ]
VOLUME [ "/server/logs" ]

EXPOSE 25565
ENTRYPOINT [ "/bin/sh" ]
CMD [ "start.sh" ]
