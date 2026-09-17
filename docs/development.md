# Native builds and releases

`scripts/upstream.json` pins shaderc v2025.1 and the glslang, SPIRV-Tools, and
SPIRV-Headers commits from that release's `DEPS`. Update those pins together.
Tests and examples in upstream projects are disabled; their test-only
dependencies are not downloaded. Only the `shaderc_shared` target is built.

```sh
python3 scripts/build_native.py --jobs 2
python3 -B -m unittest discover -s tests -v
python3 scripts/smoke.py
python3 scripts/package_release.py --target linux-x64 --version dev
```

Windows uses the same commands with `python` and `--target windows-x64` for
packaging. Install Visual Studio 2022's x64 C++ tools and C3 0.8.3 first. Builds
write the libraries to `linux/` or `windows/` and their provenance and licenses to
`native-info/<target>/`; all are ignored by Git. `--work-dir` and `--output` on the
build script can redirect the cache and native output.

The smoke consumer compiles GLSL into SPIR-V with optimization and a macro,
checks the SPIR-V header, and verifies diagnostics for invalid GLSL. It requires
no Vulkan SDK or GPU. The harness isolates the dependency search directory and
loads the selected native library, including when testing an extracted bundle:

```sh
python3 -m zipfile -e dist/shaderc.c3l-dev-linux-x64.zip build/consumer
python3 scripts/smoke.py --library build/consumer/shaderc.c3l
```

Every branch push, pull request, or manual workflow run builds and runs this
consumer on Ubuntu 22.04 and Windows Server 2022, then repeats it against the
extracted platform bundle. CI artifacts named `shaderc-linux-x64` and
`shaderc-windows-x64` contain the native files, a platform bundle, native
provenance/licenses, and `SHA256SUMS`.

To publish a release, tag the intended binding commit `vX.Y.Z` and push the tag.
The release job waits for both platform jobs to pass, verifies their downloaded
assets through the same consumer fetch helper, and assembles:

- `shaderc.c3l-vX.Y.Z.zip`, containing both platforms and the C3 binding.
- Three individually downloadable native libraries.
- `shaderc-native-info-linux-x64.zip` and `shaderc-native-info-windows-x64.zip`.
- `SHA256SUMS` covering all of the above.

Only the tag release job receives `contents: write`. It creates a new release;
it does not overwrite an existing release's assets. The source-only migration
does not rewrite old Git history or remove binaries from old tags.
