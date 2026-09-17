# shaderc.c3l

C3 binding for [shaderc](https://github.com/google/shaderc) — runtime GLSL to SPIR-V
compilation on Linux x64 and Windows x64. Tested with C3 0.8.3.

Native libraries are built by CI from pinned sources and distributed as CI
artifacts and GitHub release assets. The Git checkout contains no native binaries.

## Install

Download `shaderc.c3l-<tag>.zip` and `SHA256SUMS` from the matching
[release](https://github.com/fesoliveira014/shaderc.c3l/releases), verify the ZIP's
SHA-256 against `SHA256SUMS`, then extract it into your dependency search path:

```sh
unzip shaderc.c3l-<tag>.zip -d lib
```

The bundle contains `lib/shaderc.c3l/`, including both platforms' libraries,
the binding, and native licenses. Use this uploaded bundle; GitHub's automatic
"Source code" archives contain no binaries.

### Git submodule

Check out a release tag, then fetch the native library for your host with Python
3.10 or newer:

```sh
git submodule add https://github.com/fesoliveira014/shaderc.c3l lib/shaderc.c3l
git -C lib/shaderc.c3l checkout <tag>
python3 lib/shaderc.c3l/scripts/fetch_native_libs.py
```

On Windows, use `python` in place of `python3`. The helper defaults to the exact
tag of the binding checkout and checks every asset against the release's
`SHA256SUMS` before installing it. Use `--target all` to install both platforms or
`--target windows-x64` to prepare a Windows package from Linux. An explicit tag
can be passed as the first argument; choose one compatible with your binding.

Development commits, and checkouts before the first release, can build the
pinned native library locally:

```sh
python3 lib/shaderc.c3l/scripts/build_native.py
```

This requires Git, CMake 3.22.1+, Python 3.10+, and a C++17 compiler. Linux uses
the default CMake generator; Windows uses Visual Studio 2022 with the x64 C++
tools. Sources and build output are cached under `build/native/`.

## Use

In `project.json`:

```json
"dependency-search-paths": [ "lib" ],
"dependencies": [ "shaderc" ]
```

```c3
import shaderc;
shaderc::Compiler compiler = shaderc::compiler_create();
defer compiler.release();
```

## Runtime libraries

| Target | Installed files | Runtime setup |
| --- | --- | --- |
| `linux-x64` | `linux/libshaderc_shared.so.1` | Ship the `.so` and set an appropriate executable RUNPATH, or add its directory to `LD_LIBRARY_PATH` during development. |
| `windows-x64` | `windows/shaderc_shared.lib`, `windows/shaderc_shared.dll` | Ship the DLL beside your executable. The `.lib` is an MSVC import library used at link time. |

The existing library paths and manifest link names are preserved. CI builds
Linux on Ubuntu 22.04 (glibc 2.35); the library also uses the system C++ runtime.
Windows builds use the static MSVC CRT inside the DLL. No Vulkan SDK, Vulkan
driver, or GPU is needed to compile shaders with this package.

Each release also provides `libshaderc_shared-linux-x64.so.1`,
`shaderc_shared-windows-x64.dll`, `shaderc_shared-windows-x64.lib`, and
`shaderc-native-info-<target>.zip` for manual installation. Rename the platform
suffixes away when installing individual libraries to the paths above. The
download helper handles this and installs the native source revisions and
licenses under `native-info/<target>/`.

## License

The binding is MIT-licensed (`LICENSE`). Shaderc is Apache-2.0 licensed
(`LICENSE.shaderc.apache-2.0`); native distributions also include the glslang,
SPIRV-Tools, and SPIRV-Headers licenses. Retain these notices when redistributing
the libraries; see `NOTICE` and `native-info/<target>/` in the release bundle.
