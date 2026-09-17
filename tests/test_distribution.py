import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = {
    "libshaderc_shared-linux-x64.so.1": "linux/libshaderc_shared.so.1",
    "shaderc_shared-windows-x64.dll": "windows/shaderc_shared.dll",
    "shaderc_shared-windows-x64.lib": "windows/shaderc_shared.lib",
}


class DistributionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.native = self.root / "native"
        self.release = self.root / "release"
        self.consumer = self.root / "consumer.c3l"
        self.release.mkdir()
        self.consumer.mkdir()
        for name, path in ASSETS.items():
            output = self.native / path
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(name.encode())
        for target in ("linux-x64", "windows-x64"):
            info = self.native / "native-info" / target
            info.mkdir(parents=True)
            (info / "BUILD.json").write_text(json.dumps({"target": target}))
            for project in ("shaderc", "glslang", "spirv-tools", "spirv-headers"):
                (info / f"LICENSE.{project}").write_text(f"License for {project}\n")

    def package(self, target="all"):
        return subprocess.run([
            sys.executable, str(ROOT / "scripts/package_release.py"),
            "--native-dir", str(self.native), "--output", str(self.release),
            "--version", "v0.1.0", "--target", target,
        ], capture_output=True, text=True)

    def fetch(self, target="all"):
        return subprocess.run([
            sys.executable, str(ROOT / "scripts/fetch_native_libs.py"), "v0.1.0",
            "--target", target, "--destination", str(self.consumer),
            "--base-url", self.release.as_uri(),
        ], capture_output=True, text=True)

    def test_bundle_is_complete_and_reproducible(self):
        result = self.package()
        self.assertEqual(result.returncode, 0, result.stderr)
        archive = self.release / "shaderc.c3l-v0.1.0.zip"
        original = archive.read_bytes()
        with zipfile.ZipFile(archive) as bundle:
            names = set(bundle.namelist())
            for path in (*ASSETS.values(), "manifest.json", "shaderc.c3i", "NOTICE",
                         "LICENSE", "LICENSE.shaderc.apache-2.0", "README.md",
                         "native-info/linux-x64/BUILD.json",
                         "native-info/windows-x64/LICENSE.glslang"):
                self.assertIn(f"shaderc.c3l/{path}", names)
            self.assertFalse(any("/tests/" in name or "/scripts/" in name for name in names))
        result = self.package()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(original, archive.read_bytes())
        for line in (self.release / "SHA256SUMS").read_text().splitlines():
            digest, name = line.split()
            self.assertEqual(digest, hashlib.sha256((self.release / name).read_bytes()).hexdigest())

    def test_download_roundtrip(self):
        result = self.package()
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.fetch()
        self.assertEqual(result.returncode, 0, result.stderr)
        for path in ASSETS.values():
            self.assertEqual((self.consumer / path).read_bytes(), (self.native / path).read_bytes())
        self.assertTrue((self.consumer / "native-info/windows-x64/LICENSE.glslang").is_file())

    def test_corrupt_download_preserves_existing_install(self):
        result = self.package()
        self.assertEqual(result.returncode, 0, result.stderr)
        existing = self.consumer / "linux/libshaderc_shared.so.1"
        existing.parent.mkdir()
        existing.write_bytes(b"existing library")
        (self.release / "shaderc_shared-windows-x64.dll").write_bytes(b"corrupt")
        result = self.fetch()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("checksum", result.stderr.lower())
        self.assertEqual(existing.read_bytes(), b"existing library")
        self.assertFalse((self.consumer / "windows/shaderc_shared.dll").exists())

    def test_linux_assets_do_not_require_windows(self):
        result = self.package("linux-x64")
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.fetch("linux-x64")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.consumer / "windows").exists())

    def test_missing_input_does_not_publish_partial_assets(self):
        (self.native / "windows/shaderc_shared.lib").unlink()
        result = self.package()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("shaderc_shared.lib", result.stderr)
        self.assertEqual(list(self.release.iterdir()), [])

    def test_missing_license_is_rejected(self):
        (self.native / "native-info/linux-x64/LICENSE.glslang").unlink()
        result = self.package()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("LICENSE.glslang", result.stderr)
        self.assertEqual(list(self.release.iterdir()), [])

    def test_missing_checksum_is_rejected_before_install(self):
        result = self.package()
        self.assertEqual(result.returncode, 0, result.stderr)
        sums = self.release / "SHA256SUMS"
        sums.write_text("".join(line for line in sums.read_text().splitlines(keepends=True)
                                if "shaderc_shared-windows-x64.lib" not in line))
        result = self.fetch()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing checksum", result.stderr)
        self.assertEqual(list(self.consumer.iterdir()), [])

    def test_native_info_archive_cannot_write_unexpected_paths(self):
        result = self.package()
        self.assertEqual(result.returncode, 0, result.stderr)
        name = "shaderc-native-info-linux-x64.zip"
        info = self.release / name
        with zipfile.ZipFile(info, "a") as archive:
            archive.writestr("../escaped.txt", b"must not be installed")
        sums = self.release / "SHA256SUMS"
        digest = hashlib.sha256(info.read_bytes()).hexdigest()
        sums.write_text("".join(f"{digest}  {name}\n" if name in line else line
                                for line in sums.read_text().splitlines(keepends=True)))
        result = self.fetch()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unexpected native-info archive", result.stderr)
        self.assertEqual(list(self.consumer.iterdir()), [])
        self.assertFalse((self.root / "escaped.txt").exists())


if __name__ == "__main__":
    unittest.main()
