#!/usr/bin/env python3
"""Build the pinned shaderc shared library for the host (Linux/Windows x64)."""

import argparse
import json
from pathlib import Path
import shutil
import subprocess

from native import LIBRARIES, host_target


ROOT = Path(__file__).resolve().parents[1]


def run(*command, cwd=None):
    subprocess.run([str(arg) for arg in command], cwd=cwd, check=True)


def checkout(path, project):
    if not (path / ".git").exists():
        path.mkdir(parents=True, exist_ok=True)
        run("git", "init", path)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=path, capture_output=True, text=True)
    if head.returncode != 0 or head.stdout.strip() != project["revision"]:
        run("git", "fetch", "--depth=1", project["repository"], project["revision"], cwd=path)
        run("git", "checkout", "--detach", project["revision"], cwd=path)
    status = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=path, text=True)
    if status.strip():
        raise ValueError(f"upstream checkout has modified files: {path}")


def build(work, output, jobs):
    target = host_target()
    projects = json.loads((ROOT / "scripts/upstream.json").read_text())
    source = work / "shaderc"
    for project in projects.values():
        checkout(source / project["path"], project)
    binary = work / target
    configure = [
        "cmake", "-S", source, "-B", binary,
        "-DCMAKE_BUILD_TYPE=Release", "-DCMAKE_POSITION_INDEPENDENT_CODE=ON",
        "-DSHADERC_SKIP_TESTS=ON", "-DSHADERC_SKIP_EXAMPLES=ON",
        "-DSHADERC_SKIP_COPYRIGHT_CHECK=ON", "-DSHADERC_ENABLE_WERROR_COMPILE=OFF",
        "-DSPIRV_SKIP_TESTS=ON", "-DSPIRV_SKIP_EXECUTABLES=ON",
        "-DSHADERC_ENABLE_SHARED_CRT=OFF",
    ]
    if target == "windows-x64":
        configure.extend(["-G", "Visual Studio 17 2022", "-A", "x64"])
    run(*configure)
    run("cmake", "--build", binary, "--config", "Release", "--target", "shaderc_shared", "--parallel", jobs)
    library_dir = binary / "libshaderc"
    if target == "windows-x64":
        library_dir /= "Release"
    for path in LIBRARIES[target].values():
        destination = output / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(library_dir / destination.name, destination)
    info = output / "native-info" / target
    info.mkdir(parents=True, exist_ok=True)
    for name, project in projects.items():
        shutil.copyfile(source / project["path"] / project["license"], info / f"LICENSE.{name}")
    cache = (binary / "CMakeCache.txt").read_text()
    compiler = [line for line in cache.splitlines() if line.startswith((
        "CMAKE_CXX_COMPILER:", "CMAKE_C_COMPILER:", "CMAKE_GENERATOR:", "CMAKE_BUILD_TYPE:"))]
    (info / "BUILD.json").write_text(json.dumps({
        "target": target, "upstream": projects, "cmake": compiler,
        "configuration": "Release", "windows_crt": "static" if target == "windows-x64" else None,
    }, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, default=ROOT / "build/native")
    parser.add_argument("--output", type=Path, default=ROOT)
    parser.add_argument("--jobs", type=int, default=2)
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error("--jobs must be positive")
    try:
        build(args.work_dir.resolve(), args.output.resolve(), args.jobs)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"error: {error}\n")


if __name__ == "__main__":
    main()
