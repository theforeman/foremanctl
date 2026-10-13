#!/usr/bin/env python3
"""Build and load a Foreman image containing packages from a Packit PR."""

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
CONTAINERFILE = SCRIPT_DIR / "Containerfile"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-image", default="quay.io/foreman/foreman:nightly")
    parser.add_argument("--repo-org", default="theforeman")
    parser.add_argument("--repo-name", default="foreman")
    parser.add_argument("--pr", required=True, help="Packit pull request number")
    return parser.parse_args()


def get_container_user(base_image: str) -> str:
    """Read the configured user from a local base image, pulling it if needed."""
    inspect_command = [
        "podman",
        "image",
        "inspect",
        "--format",
        "{{.Config.User}}",
        base_image,
    ]
    try:
        result = subprocess.run(inspect_command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError:
        subprocess.run(["podman", "pull", base_image], check=True)
        result = subprocess.run(inspect_command, check=True, capture_output=True, text=True)

    # An unset image user means the container runs as root.
    return result.stdout.strip() or "0"


def build_image(args: argparse.Namespace, container_user: str) -> None:
    command = [
        "podman",
        "build",
        "--file",
        str(CONTAINERFILE),
        "--build-arg",
        f"BASE_IMAGE={args.base_image}",
        "--build-arg",
        f"CONTAINER_USER={container_user}",
        "--build-arg",
        f"REPO_ORG={args.repo_org}",
        "--build-arg",
        f"REPO_NAME={args.repo_name}",
        "--build-arg",
        f"PR={args.pr}",
        "--tag",
        args.base_image,
        str(SCRIPT_DIR),
    ]
    subprocess.run(command, check=True)


def load_image_as_root(image: str) -> int:
    """Pipe the user's image store into root's Podman image store."""
    save_process = subprocess.Popen(["podman", "save", image], stdout=subprocess.PIPE)
    assert save_process.stdout is not None

    try:
        load_process = subprocess.Popen(["sudo", "podman", "load"], stdin=save_process.stdout)
    except OSError:
        save_process.stdout.close()
        save_process.wait()
        raise

    # Let the load process consume the pipe; otherwise save can wait forever
    # for the parent to close its copy of the read end.
    save_process.stdout.close()
    load_status = load_process.wait()
    save_status = save_process.wait()

    if load_status != 0:
        return load_status
    return save_status


def main() -> int:
    args = parse_args()
    try:
        container_user = get_container_user(args.base_image)
        build_image(args, container_user)
        return load_image_as_root(args.base_image)
    except subprocess.CalledProcessError as error:
        return error.returncode
    except OSError as error:
        print(f"Unable to run Podman command: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
