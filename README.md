# shaderc.c3l

C3 binding for [shaderc](https://github.com/google/shaderc), providing runtime
GLSL to SPIR-V compilation on Linux x64 and Windows x64. Tested with C3 0.8.3.

Native binaries are built by CI and distributed through
[releases](https://github.com/fesoliveira014/shaderc.c3l/releases). They are not
stored in Git.

## Install

Each release publishes one artifact per platform and a `SHA256SUMS` file:

- `shaderc-v<version>-linux-x64.c3l`
- `shaderc-v<version>-windows-x64.c3l`

An artifact is a zip with `manifest.json` at its root. Verify it with
`sha256sum -c SHA256SUMS` and place it in a directory listed under
`dependency-search-paths`, for example `lib/`. Keep one platform's artifact per
directory. GitHub's automatic "Source code" downloads contain no native
libraries.

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

The shared library must sit next to the executable on both platforms. After a
build, c3c unpacks the artifact to
`<output>/unpacked_c3l/shaderc-v<version>-<platform>.c3l/`; copy the library
from its `linux/` or `windows/` directory, or unzip it from the artifact.

- **Linux:** copy `linux/libshaderc_shared.so.1`. The manifest sets the
  executable's RUNPATH to `$ORIGIN`. CI builds on Ubuntu 22.04; the library uses
  the system C++ runtime.
- **Windows:** `windows/shaderc_shared.lib` is the import library used at link
  time. Copy `windows/shaderc_shared.dll`.

No Vulkan SDK, Vulkan driver, or GPU is needed to compile shaders.

## License

The binding is MIT-licensed (`LICENSE`); shaderc is Apache-2.0 licensed
(`LICENSE.shaderc.apache-2.0`). Artifacts include the glslang, SPIRV-Tools, and
SPIRV-Headers licenses under `licenses/`. Keep these notices when redistributing
binaries; see `NOTICE`.
