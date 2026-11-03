"""The compatibility package must never replace QSDK's original library."""

import hashlib
import importlib.util
import io
from pathlib import Path
import tarfile
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    "qwrt_compat", Path(__file__).resolve().parents[1] / "dev/qwrt/build-libnl-compat.py"
)
compat = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compat)


class CompatPackageTest(unittest.TestCase):
    def source(self, files):
        return compat.archive({"data.tar.gz": compat.archive(files)})

    def build_fixture(self, source):
        # Production accepts only the pinned upstream digest. Fixtures exercise
        # archive handling separately, with their own explicit trust anchor.
        with patch.object(compat, "SOURCE_SHA256", hashlib.sha256(source).hexdigest()):
            return compat.build_package(source)

    def test_rejects_unverified_download(self):
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            compat.build_package(b"damaged download")

    def test_owns_only_the_versioned_library_and_preserves_its_payload(self):
        source = self.source({compat.LIBRARY: b"library fixture"})
        package = self.build_fixture(source)
        self.assertEqual(package, self.build_fixture(source))
        with tarfile.open(fileobj=io.BytesIO(source)) as src, tarfile.open(fileobj=io.BytesIO(package)) as pkg:
            self.assertEqual(pkg.extractfile("./data.tar.gz").read(), src.extractfile("./data.tar.gz").read())
            control = pkg.extractfile("./control.tar.gz").read()
        with tarfile.open(fileobj=io.BytesIO(control)) as tar:
            metadata = tar.extractfile("./control").read().decode()
        self.assertIn("Package: vantage-qwrt-libnl-compat\n", metadata)
        self.assertNotIn("Provides:", metadata)
        self.assertNotIn("Replaces:", metadata)

    def test_rejects_payloads_that_could_overwrite_existing_system_files(self):
        for files in [
            {"usr/lib/libnl-tiny.so": b"wrong soname"},
            {compat.LIBRARY: b"library", "etc/config/network": b"unrelated file"},
            {"../usr/lib/libnl-tiny.so.1": b"path traversal"},
        ]:
            with self.subTest(files=list(files)), self.assertRaisesRegex(ValueError, "only the versioned"):
                self.build_fixture(self.source(files))


if __name__ == "__main__":
    unittest.main()
