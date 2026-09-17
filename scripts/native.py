"""Shared release layout for the builder, packager, and downloader."""

import platform


LIBRARIES = {
    "linux-x64": {"libshaderc_shared-linux-x64.so.1": "linux/libshaderc_shared.so.1"},
    "windows-x64": {
        "shaderc_shared-windows-x64.dll": "windows/shaderc_shared.dll",
        "shaderc_shared-windows-x64.lib": "windows/shaderc_shared.lib",
    },
}
PROJECTS = ("shaderc", "glslang", "spirv-tools", "spirv-headers")


def host_target():
    if platform.machine().lower() not in ("amd64", "x86_64"):
        raise ValueError("only x86-64 Linux and Windows native libraries are provided")
    targets = {"Linux": "linux-x64", "Windows": "windows-x64"}
    try:
        return targets[platform.system()]
    except KeyError:
        raise ValueError("only x86-64 Linux and Windows native libraries are provided") from None


def targets_for(target):
    return list(LIBRARIES) if target == "all" else [host_target() if target == "auto" else target]


def info_paths(target):
    return [f"native-info/{target}/{name}" for name in
            ("BUILD.json", *(f"LICENSE.{project}" for project in PROJECTS))]


def info_asset(target):
    return f"shaderc-native-info-{target}.zip"
