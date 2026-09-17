#!/usr/bin/env python3
"""Compile and run a C3 consumer using only the selected library directory."""

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from native import LIBRARIES, host_target


ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, default=ROOT)
    args = parser.parse_args()
    library = args.library.resolve()
    target = host_target()
    with tempfile.TemporaryDirectory(prefix="shaderc-smoke-") as temp:
        work = Path(temp)
        dependency = work / "lib/shaderc.c3l"
        dependency.mkdir(parents=True)
        for path in ("manifest.json", "shaderc.c3i", *LIBRARIES[target].values()):
            output = dependency / path
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(library / path, output)
        executable = work / ("smoke.exe" if target == "windows-x64" else "smoke")
        subprocess.run([
            "c3c", "compile", str(ROOT / "tests/smoke.c3"), "--libdir", str(dependency.parent),
            "--lib", "shaderc", "--warn-deprecation=error", "-o", str(executable),
        ], cwd=work, check=True)
        env = os.environ.copy()
        if target == "windows-x64":
            shutil.copyfile(dependency / "windows/shaderc_shared.dll", work / "shaderc_shared.dll")
        else:
            env["LD_LIBRARY_PATH"] = str(dependency / "linux")
        subprocess.run([str(executable)], cwd=work, env=env, check=True)


if __name__ == "__main__":
    main()
