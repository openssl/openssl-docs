FROM docker.io/library/pypy:3.11-slim-bookworm AS BASE

# minify-html ships no PyPy wheels, so it is compiled from source here and needs a
# Rust toolchain plus the C runtime headers for the linker. Everything from this
# stage except /docs_venv is discarded.
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libc6-dev curl ca-certificates && \
    curl -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal

ENV PATH=/docs_venv/bin:/root/.cargo/bin:$PATH

COPY requirements.txt /requirements.txt

RUN python3 -m venv /docs_venv && \
    pip install --no-binary minify-html -r /requirements.txt && \
    chmod -R a+rwX /docs_venv

FROM docker.io/library/pypy:3.11-slim-bookworm

RUN apt-get update && \
    apt-get install -y --no-install-recommends cpanminus gcc git make && \
    cpanm Pod::Markdown@3.400 && \
    apt-get purge -y cpanminus && \
    apt-get autoremove -y && \
    apt-get clean

COPY --from=BASE /docs_venv /docs_venv

# COPY recreates the target directory itself with default permissions; its contents
# were already made writable in the BASE stage.
RUN chmod a+rwX /docs_venv

ENV PATH=/docs_venv/bin:$PATH \
    GIT_COMMITTER_NAME=openssl-machine \
    GIT_COMMITTER_EMAIL=openssl-machine@openssl.org

RUN useradd -m openssl-docs

USER openssl-docs
