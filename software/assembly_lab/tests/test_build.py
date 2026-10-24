"""Hermetic regression tests for release packaging."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile


MODULE = Path(__file__).resolve().parents[1]
SOURCE_FILES = (
    "build_release.py", "README.md", "index.html.in", "style.css", "core.js", "app.js",
    "assets/chassis.png", "assets/model.json.gz", "assets/provenance.json",
)


class BuildReleaseTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="kitty-assembly-build-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.repository = self.root / "repository"
        self.source = self.repository / "software/assembly_lab"
        for name in SOURCE_FILES:
            target = self.source / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(MODULE / name, target)
        self.vendor = self.repository / "design/v7/advanced-viewer/vendor"
        vendor = MODULE / "vendor"
        if not vendor.exists():
            vendor = MODULE.parents[1] / "design/v7/advanced-viewer/vendor"
        shutil.copytree(vendor, self.vendor)

    def build(self, output, *, archive=False, source=None):
        source = source or self.source
        command = [sys.executable, "-B", str(source / "build_release.py"),
                   "--out", str(output)]
        if archive:
            command.append("--archive")
        return subprocess.run(command, cwd=source, capture_output=True,
                              text=True, encoding="utf-8", timeout=30)

    def assert_build_succeeds(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def source_snapshot(self):
        return {str(path.relative_to(self.source)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in self.source.rglob("*") if path.is_file()}

    def assert_archive(self, output, expected, verification=None):
        with zipfile.ZipFile(output / "KITTY-ASSEMBLY-LAB-COMPLETE.zip") as archive:
            self.assertIsNone(archive.testzip())
            names = archive.namelist()
            expected_names = {"KITTY-ASSEMBLY-LAB.html", "START-HERE.md", "BUILD-PROVENANCE.json"}
            expected_names.update("source/" + name for name in expected)
            expected_names.update("source/vendor/" + path.name for path in self.vendor.iterdir())
            if verification:
                expected_names.add(verification.name)
                self.assertEqual(archive.read(verification.name), verification.read_bytes())
            self.assertEqual(set(names), expected_names)
            self.assertEqual(len(names), len(set(names)))
            self.assertFalse(any(name.endswith(".zip") for name in names))
            for name, digest in expected.items():
                self.assertEqual(hashlib.sha256(archive.read("source/" + name)).hexdigest(), digest)
            for path in self.vendor.iterdir():
                self.assertEqual(archive.read("source/vendor/" + path.name), path.read_bytes())
            for name in ("KITTY-ASSEMBLY-LAB.html", "START-HERE.md", "BUILD-PROVENANCE.json"):
                self.assertEqual(archive.read(name), (output / name).read_bytes())
            evidence = json.loads(archive.read("BUILD-PROVENANCE.json"))
            self.assertEqual(evidence["source_sha256"], expected)
            self.assertEqual(evidence["html_sha256"],
                             hashlib.sha256(archive.read("KITTY-ASSEMBLY-LAB.html")).hexdigest())

    def test_nested_output_is_excluded_from_source_hashes(self):
        expected = self.source_snapshot()
        self.assert_build_succeeds(self.build("dist"))
        output = self.source / "dist"
        evidence = json.loads((output / "BUILD-PROVENANCE.json").read_text(encoding="utf-8"))
        generated = [name for name in evidence["source_sha256"] if name.startswith("dist/")]
        self.assertEqual(generated, [], "Generated output entered source_sha256")
        self.assertEqual(evidence["source_sha256"], expected)

    def test_source_root_output_is_rejected_before_writes(self):
        expected = self.source_snapshot()
        for output in (".", "missing/..", self.source):
            with self.subTest(output=str(output)):
                result = self.build(output, archive=True)
                self.assertNotEqual(result.returncode, 0, "Builder accepted its source directory as output")
                self.assertIn("source directory", result.stderr)
                self.assertEqual(self.source_snapshot(), expected)
                self.assertFalse((self.source / "missing").exists())

    def test_nested_archive_excludes_output_and_open_zip(self):
        expected = self.source_snapshot()
        output = self.source / "dist"
        stale = output / "cache/stale.txt"
        stale.parent.mkdir(parents=True)
        stale.write_text("Prior output must stay out of the source archive", encoding="utf-8")
        (output / "KITTY-ASSEMBLY-LAB-COMPLETE.zip").write_bytes(b"prior archive")
        verification = output / "BROWSER-VERIFICATION.json"
        verification.write_text('{"fixture": true}\n', encoding="utf-8")
        self.assert_build_succeeds(self.build("dist", archive=True))
        self.assert_archive(output, expected, verification)
        self.assertTrue(stale.is_file())
        self.assert_build_succeeds(self.build("dist", archive=True))
        self.assert_archive(output, expected, verification)

    def test_external_archive_preserves_sources_and_rebuilds_portably(self):
        expected = self.source_snapshot()
        output = self.root / "external-release"
        self.assert_build_succeeds(self.build(output, archive=True))
        self.assert_archive(output, expected)
        extracted = self.root / "extracted"
        with zipfile.ZipFile(output / "KITTY-ASSEMBLY-LAB-COMPLETE.zip") as archive:
            archive.extractall(extracted)
        rebuilt = self.root / "rebuilt-release"
        self.assert_build_succeeds(self.build(rebuilt, source=extracted / "source"))
        self.assertEqual((rebuilt / "KITTY-ASSEMBLY-LAB.html").read_bytes(),
                         (output / "KITTY-ASSEMBLY-LAB.html").read_bytes())

    def test_output_above_source_keeps_source_files(self):
        expected = self.source_snapshot()
        self.assert_build_succeeds(self.build(self.repository, archive=True))
        self.assert_archive(self.repository, expected)

    def test_changed_asset_still_fails_integrity_check(self):
        asset = self.source / "assets/chassis.png"
        asset.write_bytes(asset.read_bytes() + b"changed")
        output = self.root / "invalid-release"
        result = self.build(output, archive=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Asset changed: chassis.png", result.stderr)
        self.assertFalse((output / "KITTY-ASSEMBLY-LAB.html").exists())
        self.assertFalse((output / "KITTY-ASSEMBLY-LAB-COMPLETE.zip").exists())


if __name__ == "__main__":
    unittest.main()
