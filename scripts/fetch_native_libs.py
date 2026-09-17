#!/usr/bin/env python3
"""Install checksum-verified shaderc release libraries into a source checkout."""

import argparse
import hashlib
import io
from pathlib import Path
import re
import subprocess
import tempfile
import urllib.request
import zipfile

from native import LIBRARIES, info_asset, info_paths, targets_for


ROOT = Path(__file__).resolve().parents[1]
RELEASES = "https://github.com/fesoliveira014/shaderc.c3l/releases/download"


def download(url):
    with urllib.request.urlopen(url, timeout=120) as response:
        return response.read()


def install(destination, target, base_url):
    checksums = {}
    for line in download(f"{base_url}/SHA256SUMS").decode().splitlines():
        fields = line.split()
        if len(fields) != 2 or not re.fullmatch(r"[0-9a-f]{64}", fields[0]):
            raise ValueError("invalid SHA256SUMS entry")
        digest, name = fields
        if name in checksums:
            raise ValueError(f"duplicate checksum for {name}")
        checksums[name] = digest

    def verified(asset):
        if asset not in checksums:
            raise ValueError(f"missing checksum for {asset}")
        payload = download(f"{base_url}/{asset}")
        if hashlib.sha256(payload).hexdigest() != checksums[asset]:
            raise ValueError(f"checksum mismatch for {asset}")
        return payload

    files = {}
    for platform in targets_for(target):
        for asset, path in LIBRARIES[platform].items():
            files[path] = verified(asset)
        with zipfile.ZipFile(io.BytesIO(verified(info_asset(platform)))) as info:
            expected = info_paths(platform)
            if sorted(info.namelist()) != sorted(expected):
                raise ValueError(f"unexpected native-info archive contents for {platform}")
            for path in expected:
                files[path] = info.read(path)

    # Validate every download before replacing any installed file.
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".shaderc-", dir=destination) as temp:
        staging = Path(temp)
        for path, payload in files.items():
            staged = staging / path
            staged.parent.mkdir(parents=True, exist_ok=True)
            staged.write_bytes(payload)
        for path in files:
            output = destination / path
            output.parent.mkdir(parents=True, exist_ok=True)
            (staging / path).replace(output)
            print(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag", nargs="?", help="release tag (default: exact tag of this checkout)")
    parser.add_argument("--target", choices=["auto", "all", *LIBRARIES], default="auto")
    parser.add_argument("--destination", type=Path, default=ROOT)
    parser.add_argument("--base-url", help="override the release asset URL, including file:// for offline use")
    args = parser.parse_args()
    try:
        tag = args.tag
        if not tag:
            result = subprocess.run(["git", "describe", "--tags", "--exact-match"],
                                    cwd=ROOT, capture_output=True, text=True, check=True)
            tag = result.stdout.strip()
        if not re.fullmatch(r"v[0-9][A-Za-z0-9._-]*", tag):
            raise ValueError("expected a version tag such as v0.1.0")
        install(args.destination.resolve(), args.target, (args.base_url or f"{RELEASES}/{tag}").rstrip("/"))
    except subprocess.CalledProcessError:
        parser.exit(1, "error: checkout is not on a release tag; pass a tag or build with scripts/build_native.py\n")
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        parser.exit(1, f"error: {error}\n")


if __name__ == "__main__":
    main()
