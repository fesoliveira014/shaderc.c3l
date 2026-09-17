# shaderc.c3l

C3 binding for [shaderc](https://github.com/google/shaderc), providing runtime
GLSL to SPIR-V compilation on Linux x64 and Windows x64. Tested with C3 0.8.3.

Native binaries are built by CI and distributed through
[releases](https://github.com/fesoliveira014/shaderc.c3l/releases). They are not
stored in Git.

## Install

Download the bundle for your platform and its `.sha256` file from the same
release:

- `shaderc.c3l-linux-x64.tar.gz`
- `shaderc.c3l-windows-x64.tar.gz`

Each bundle contains `shaderc.c3l/` with the binding, native libraries, and
licenses. Verify and extract it into your dependency search path. For Linux:

```sh
sha256sum -c shaderc.c3l-linux-x64.tar.gz.sha256
mkdir -p lib
tar -xzf shaderc.c3l-linux-x64.tar.gz -C lib
```

On Windows, compare `Get-FileHash shaderc.c3l-windows-x64.tar.gz -Algorithm SHA256`
with the downloaded `.sha256` file, then extract with `tar -xzf` as above.

For a Git submodule, check out the matching release tag and extract the bundle
into the submodule's parent directory (for example, `lib/`). GitHub's automatic
"Source code" downloads contain no native libraries. Before a release is
available, the same bundles can be downloaded from a successful CI run's
artifacts.

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

- **Linux:** ship `linux/libshaderc_shared.so.1` and configure your executable's
  RUNPATH or `LD_LIBRARY_PATH` to find it. CI builds on Ubuntu 22.04; the library
  uses the system C++ runtime.
- **Windows:** `windows/shaderc_shared.lib` is the import library used at link
  time. Ship `windows/shaderc_shared.dll` beside your executable.

No Vulkan SDK, Vulkan driver, or GPU is needed to compile shaders.

## License

The binding is MIT-licensed (`LICENSE`); shaderc is Apache-2.0 licensed
(`LICENSE.shaderc.apache-2.0`). Bundles include the glslang, SPIRV-Tools, and
SPIRV-Headers licenses under `licenses/`. Keep these notices when redistributing
binaries; see `NOTICE`.
