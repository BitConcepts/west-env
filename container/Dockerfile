# SPDX-License-Identifier: Apache-2.0

FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive

# ------------------------------------------------------------
# Base system & build dependencies
# ------------------------------------------------------------
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        sudo \
        git \
        cmake \
        ninja-build \
        gperf \
        ccache \
        dfu-util \
        device-tree-compiler \
        wget \
        python3 \
        python3-pip \
        python3-dev \
        python3-venv \
        python3-tk \
        xz-utils \
        file \
        make \
        gcc \
        gcc-multilib \
        g++-multilib \
        libsdl2-dev \
        libmagic1 && \
    rm -rf /var/lib/apt/lists/*

# ------------------------------------------------------------
# Python tooling (system Python, no venv)
# ------------------------------------------------------------
RUN python3 -m pip install --no-cache-dir --upgrade pip && \
    python3 -m pip install --no-cache-dir west

# ------------------------------------------------------------
# Zephyr SDK
# ------------------------------------------------------------
ARG ZEPHYR_SDK_VERSION=0.17.4
ENV ZEPHYR_SDK_INSTALL_DIR=/opt/zephyr-sdk

RUN wget -q https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v${ZEPHYR_SDK_VERSION}/zephyr-sdk-${ZEPHYR_SDK_VERSION}_linux-x86_64.tar.xz && \
    mkdir -p ${ZEPHYR_SDK_INSTALL_DIR} && \
    tar -xf zephyr-sdk-${ZEPHYR_SDK_VERSION}_linux-x86_64.tar.xz -C ${ZEPHYR_SDK_INSTALL_DIR} --strip-components=1 && \
    rm zephyr-sdk-${ZEPHYR_SDK_VERSION}_linux-x86_64.tar.xz && \
    ${ZEPHYR_SDK_INSTALL_DIR}/setup.sh -t all -h -c

ENV ZEPHYR_TOOLCHAIN_VARIANT=zephyr
ENV ZEPHYR_SDK_INSTALL_DIR=${ZEPHYR_SDK_INSTALL_DIR}

# ------------------------------------------------------------
# Zephyr Python requirements (AUTHORITATIVE)
# ------------------------------------------------------------
# We temporarily clone Zephyr only to install its Python deps,
# then remove it to keep the image clean.
#
# This guarantees compatibility with Zephyr v4.3.0 and avoids
# guessing missing dependencies (jsonschema, pyelftools, etc.).
# ------------------------------------------------------------
ARG ZEPHYR_VERSION=v4.3.0

RUN git clone --depth 1 --branch ${ZEPHYR_VERSION} \
        https://github.com/zephyrproject-rtos/zephyr.git /tmp/zephyr && \
    python3 -m pip install --no-cache-dir \
        -r /tmp/zephyr/scripts/requirements.txt && \
    rm -rf /tmp/zephyr

# ------------------------------------------------------------
# Defaults
# ------------------------------------------------------------
WORKDIR /work
CMD ["/bin/bash"]
