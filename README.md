# shaderc.c3l

C3 binding for [shaderc](https://github.com/google/shaderc) — runtime GLSL→SPIR-V
compilation. Vendors `libshaderc_shared.so.1` (Linux).

The binding is MIT-licensed; the vendored library is Apache-2.0 (see `NOTICE`).

## Use (git submodule)

```sh
git submodule add https://github.com/fesoliveira014/shaderc.c3l lib/shaderc.c3l
```

Then in `project.json`:

```json
"dependency-search-paths": [ "lib" ],
"dependencies": [ "shaderc" ]
```

```c3
import shaderc;
shaderc::Compiler compiler = shaderc::compiler_create();
defer compiler.release();
```
