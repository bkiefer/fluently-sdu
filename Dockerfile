FROM openjdk:11-jre-slim

# Set environment

# RUN apt -q -qq update && \
#   DEBIAN_FRONTEND=noninteractive apt install -y \
#   apt-utils \
#     libasound2 \
#   	libdbus-glib-1-2 \
#   	libgtk-3-0 \
#   	libgl1-mesa-dri \
#   	libgl1-mesa-glx \
#   	libxrender1 \
#   	libx11-xcb-dev \
#   	libx11-xcb1 \
#   	libxt6 \
#   	libpulse0 \
#   	libcanberra-gtk-module \
#   	libcanberra-gtk3-module \
#   	xz-utils \
#   	--no-install-recommends

ENV JAVA_HOME=/opt/jdk

ENV PATH=${PATH}:${JAVA_HOME}/bin

WORKDIR /app

COPY src/main/resources /app/src/main/resources
COPY startnlu.sh /app/startnlu.sh
COPY target/fluently_sdu_nlu.jar /app/fluently_sdu_nlu.jar

ENTRYPOINT ["/bin/bash", "-c", "./startnlu.sh"]