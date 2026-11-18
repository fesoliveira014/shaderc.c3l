# shaderc.c3l

C3 binding for [shaderc](https://github.com/google/shaderc), providing runtime
GLSL to SPIR-V compilation on Linux x64 and Windows x64. Tested with C3 0.8.5_1.

shaderc is linked statically: each release carries one combined static library
(shaderc, glslang, SPIRV-Tools and SPIRV-Headers) per platform, built by CI and
distributed through
[releases](https://github.com/fesoliveira014/shaderc.c3l/releases). The
libraries are not stored in Git, and no shared library is shipped, so nothing
has to sit next to the executable.

## Install

Each release publishes one artifact per platform and a `SHA256SUMS` file:

- `shaderc-v<version>-linux-x64.c3l`
- `shaderc-v<version>-windows-x64.c3l`

An artifact is a zip with `manifest.json` at its root and the static library
under `linked-libs/<platform>/`. Verify it with `sha256sum -c SHA256SUMS` and
place it in a directory listed under `dependency-search-paths`, for example
`lib/`. Keep one platform's artifact per directory. GitHub's automatic "Source
code" downloads contain no native libraries.

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

`tests/static_proof.c3` compiles a vertex shader, a fragment shader with
`discard`, a compute shader that `#include`s through the include callbacks, and
a shader with a syntax error reported as `file:line`.

## Native libraries

- **Linux:** `linked-libs/linux-x64/libshaderc_combined.a`, built on Ubuntu 22.04
  with GCC as position-independent code (the executables link as PIE) and
  stripped of debug info. The manifest links `stdc++`, `m` and `pthread`; the
  system C++ runtime is a dynamic dependency, shaderc is not.
- **Windows:** `linked-libs/windows-x64/shaderc_combined.lib`, built with MSVC
  as `/MT` (release static CRT), without `/GL` (lld-link cannot read LTCG
  objects), with `_ITERATOR_DEBUG_LEVEL=0` and no debug info. The manifest sets
  `wincrt` to `static`.

No Vulkan SDK, Vulkan driver, or GPU is needed to compile shaders.

## Thread safety

shaderc's basic guarantee applies: concurrent use of different objects
(compilers, option sets, results) from different threads is safe; concurrent use
of one object is not. Serialize access to a shared compiler or option set.

## Bump procedure

1. Pick the shaderc release and take its commit. `utils/git-sync-deps` of that
   commit pins glslang, SPIRV-Tools and SPIRV-Headers (see its `DEPS`).
2. Set `SHADERC_REF` in `.github/workflows/release.yml` and the `vendor` block of
   `manifest.json` (the shaderc version and the four commits; CI fails when they
   disagree with what `git-sync-deps` checks out).
3. Refresh `licenses/` (the LICENSE files of glslang, SPIRV-Tools and
   SPIRV-Headers, `shaderc-DEPS`, `shaderc-revision.txt`) and the root
   `LICENSE.shaderc.apache-2.0` from the new checkout, and compare `shaderc.h` against
   `shaderc.c3i` for new or changed constants.
4. Open a pull request (the workflow builds both archives and runs
   `tests/static_proof.c3` against them), then push the next `v*` tag to publish.

## License

The binding is MIT-licensed (`LICENSE`); shaderc is Apache-2.0 licensed
(`LICENSE.shaderc.apache-2.0`). Artifacts include the license texts of shaderc,
glslang, SPIRV-Tools and SPIRV-Headers under `licenses/`. Keep these notices when
redistributing binaries; see `NOTICE`.
