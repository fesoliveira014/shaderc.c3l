# windows shaderc libs

These two files are vendored here and committed, exactly as `linux/` commits
`libshaderc_shared.so.1` from the Linux SDK. They come from a Windows Vulkan SDK
install (`C:\VulkanSDK\<ver>\Lib\shaderc_shared.lib` and
`...\Bin\shaderc_shared.dll`):

- `shaderc_shared.lib` — the MSVC **import library** for `shaderc_shared.dll`,
  from the Windows Vulkan SDK's `Lib/shaderc_shared.lib`. c3c's default Windows
  linker (lld-link, MSVC) resolves the `shaderc_shared` entry in `manifest.json`'s
  `windows-x64` `linked-libraries` from this directory — c3c auto-searches the
  `windows/` OS subdir of the `.c3l`, just as it searches `linux/` on Linux.

- `shaderc_shared.dll` — the runtime DLL, from the Windows Vulkan SDK's
  `Bin/shaderc_shared.dll`. **Unlike Linux, Windows has no `$ORIGIN` rpath**, so
  the loader cannot be pointed at this directory at runtime — it searches the
  executable's own directory and `PATH`. The DLL must therefore be **copied next
  to `c3vq.exe`** by the packaging step (the planned `build_windows.bat` that
  already stages `SDL3.dll` / `cimgui.dll` — add `shaderc_shared.dll` to that
  copy list). This mirrors the Linux side, where the `$ORIGIN/../lib/shaderc.c3l/
  linux` RUNPATH (set in `project.json`'s `linux`/`linux-release` targets) lets
  the loader find the vendored `.so` with no env vars; on Windows the equivalent
  is shipping the DLL alongside the binary.

To use the **static** shaderc instead (no DLL to ship), replace `shaderc_shared.lib`
with `shaderc_combined.lib` from the SDK and change the `windows-x64`
`linked-libraries` entry in `manifest.json` to `shaderc_combined`.

shaderc is Apache-2.0 licensed; see https://github.com/google/shaderc.
