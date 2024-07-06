FROM docker.io/library/pypy:3.10-slim-bookworm as BASE

RUN apt-get update && \
    apt-get install -y curl gcc

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

ENV PATH=/root/.cargo/bin:/docs_venv/bin:$PATH

RUN rustup install 1.79.0

COPY requirements.txt /requirements.txt

RUN python3 -m venv /docs_venv && \
    pip install -r /requirements.txt

FROM docker.io/library/pypy:3.10-slim-bookworm

RUN apt-get update && \
    apt-get install -y --no-install-recommends cpanminus gcc git make && \
    cpanm Pod::Markdown@3.400 && \
    apt-get purge -y cpanminus && \
    apt-get autoremove -y && \
    apt-get clean

COPY --from=BASE /docs_venv /docs_venv

RUN chmod -R a+rwX /docs_venv

ENV PATH=/docs_venv/bin:$PATH \
    GIT_COMMITTER_NAME=openssl-machine \
    GIT_COMMITTER_EMAIL=openssl-machine@openssl.org

RUN useradd -m openssl-docs

USER openssl-docs

RUN git config --global --add safe.directory "*"
