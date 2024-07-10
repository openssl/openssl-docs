# docs.openssl.org

OpenSSL Documentation website is based on
[Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) and
this repository contains required configuration and build scripts.

## Local development

All required dependencies are packed into a container image `quay.io/openssl-ci/docs`.
To start playing around you can spin up a container and run commands:

1. Clone the repository:

    ```sh
    git clone https://github.com/openssl/openssl-docs.git
    ```

2. Run the container:

    ```sh
    podman run -it -v $(pwd)/openssl-docs:/mnt -w /mnt -p 8000:8000 --userns=keep-id quay.io/openssl-ci/docs:latest bash
    ```

3. Build the docs:

    ```sh
    python build.py <OPENSSL VERSION>

4. Run the development web server:

    ```sh
    mike serve -a 0.0.0.0:8000
    ```

## Deployment



## References

- [MkDocs](https://www.mkdocs.org)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- [mike](https://github.com/jimporter/mike)
