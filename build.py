import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def clone(branch: str, tmp_dir: str) -> None:
    subprocess.run([
        "git",
        "clone",
        "--single-branch",
        "-b",
        branch,
        "--depth",
        "1",
        "https://github.com/openssl/openssl",
        tmp_dir
    ])


def clean_docs():
    shutil.rmtree("docs/")


def create_dirs():
    os.makedirs("docs/man1", exist_ok=True)
    os.makedirs("docs/man3", exist_ok=True)
    os.makedirs("docs/man5", exist_ok=True)
    os.makedirs("docs/man7", exist_ok=True)


def convert_pod_to_md(tmp_dir: str):
    for pod in Path(f"{tmp_dir}/docs").glob("**/*.pod"):
        target = f"docs/{pod.parts[-2]}/{pod.stem}.md"
        subprocess.run([
            "pod2markdown",
            '--man-url-prefix "../../man"',
            str(pod),
            target
        ])


def main():
    branch = sys.argv[1]
    with tempfile.TemporaryDirectory() as tmp_dir:
        clone(branch, tmp_dir)
        clean_docs()
        create_dirs()
        convert_pod_to_md(tmp_dir)


if __name__ == "__main__":
    sys.exit(main())
