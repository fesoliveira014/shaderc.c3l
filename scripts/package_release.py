#!/usr/bin/env python3
"""Assemble native assets and a ready-to-use C3 library from validated builds."""

import argparse
import hashlib
import io
from pathlib import Path
import re
import zipfile

from native import LIBRARIES, info_asset, info_paths, targets_for


ROOT = Path(__file__).resolve().parents[1]
SOURCES = ("manifest.json", "shaderc.c3i", "README.md", "LICENSE", "NOTICE",
           "LICENSE.shaderc.apache-2.0")


def archive(files):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for name, payload in sorted(files.items()):
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            entry.compress_type = zipfile.ZIP_DEFLATED
            bundle.writestr(entry, payload)
    return output.getvalue()


def read_file(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"missing, empty, or symlinked release input: {path}")
    return path.read_bytes()


def package(native_dir, output, version, target):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", version):
        raise ValueError("version must be a filename-safe tag or CI identifier")
    files = {name: read_file(ROOT / name) for name in SOURCES}
    assets = {}
    for platform in targets_for(target):
        for asset, path in LIBRARIES[platform].items():
            assets[asset] = files[path] = read_file(native_dir / path)
        info = {path: read_file(native_dir / path) for path in info_paths(platform)}
        files.update(info)
        assets[info_asset(platform)] = archive(info)
    suffix = "" if target == "all" else f"-{target}"
    assets[f"shaderc.c3l-{version}{suffix}.zip"] = archive({
        f"shaderc.c3l/{path}": payload for path, payload in files.items()
    })
    assets["SHA256SUMS"] = "".join(
        f"{hashlib.sha256(payload).hexdigest()}  {name}\n"
        for name, payload in sorted(assets.items())
    ).encode()
    output.mkdir(parents=True, exist_ok=True)
    for name, payload in assets.items():
        (output / name).write_bytes(payload)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-dir", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    parser.add_argument("--version", required=True)
    parser.add_argument("--target", choices=["all", *LIBRARIES], default="all")
    args = parser.parse_args()
    try:
        package(args.native_dir, args.output, args.version, args.target)
    except (OSError, ValueError) as error:
        parser.exit(1, f"error: {error}\n")


if __name__ == "__main__":
    main()
