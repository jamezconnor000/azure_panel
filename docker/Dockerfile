FROM ubuntu:22.04

WORKDIR /hal

RUN apt-get update && apt-get install -y \
    cmake \
    build-essential \
    sqlite3 \
    libsqlite3-dev \
    python3 \
    python3-pip \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN ./scripts/build.sh

ENV PATH="/usr/local/bin:${PATH}"
ENV LD_LIBRARY_PATH="/usr/local/lib:${LD_LIBRARY_PATH}"

CMD ["/bin/bash"]
