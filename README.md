[![Deploy site](https://github.com/openssl/openssl-docs/actions/workflows/deploy-site.yaml/badge.svg?branch=main)](https://github.com/openssl/openssl-docs/actions/workflows/deploy-site.yaml)

# docs.openssl.org

The OpenSSL Documentation website is based on
[Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) and
this repository contains the required configuration files and build scripts.
`docs.openssl.org` is hosted on GitHub Pages.

## Deployment

The website is automatically rebuilt on changes in `doc` directory of `openssl/openssl`. Then a
new commit is pushed to `gh-pages` branch which triggers
[pages-build-deployment](https://github.com/openssl/openssl-docs/actions/workflows/pages/pages-build-deployment)
GitHub Actions workflow.

To deploy documentation website manually trigger
[Deploy site](https://github.com/openssl/openssl-docs/actions/workflows/deploy-site.yaml) GitHub
Actions workflow.

## Local development

All required dependencies are packed into a container image `quay.io/openssl-ci/docs`.
To start playing around you can spin up a container and run commands:

1. Clone the repository:

    ```sh
    git clone https://github.com/openssl/openssl-docs.git
    ```

2. Run the container:

- For Podman:
    ```sh
    podman run -it -v $(pwd)/openssl-docs:/mnt -w /mnt -p 8000:8000 --userns=keep-id quay.io/openssl-ci/docs:latest bash
    ```
- For docker (mac):
    ```sh
    docker run -it -v $(pwd)/openssl-docs:/mnt -w /mnt -p 8000:8000  quay.io/openssl-ci/docs:latest bash
    ```

3. Build the docs:

    ```sh
    python build.py <OPENSSL BRANCH>
    ```

4. Run the development web server:

    ```sh
    mike serve -a 0.0.0.0:8000
    ```

## build.py

A small wrapper script to clone a specific OpenSSL branch and build a documentation website with
`mike`. Run it to build the website:

```sh
python build.py <OPENSSL BRANCH>
```

`mike` puts generated content into a separate branch `gh-pages`. Please refer `mike`
[documentation](https://github.com/jimporter/mike) for the details.

## hooks.py

All pre- and post- processing is done via `MkDocs` hooks. Please refer `MkDocs`
[documentation](https://www.mkdocs.org/dev-guide/plugins/#events) for the details.


## References

- [MkDocs](https://www.mkdocs.org)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- [mike](https://github.com/jimporter/mike)
