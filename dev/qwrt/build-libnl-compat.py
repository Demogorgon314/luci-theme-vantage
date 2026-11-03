#!/usr/bin/env python3
"""Repackage a pinned ARM64 library beside QSDK's existing libnl-tiny.

The library payload stays byte-identical to ImmortalWrt's package. Only the
package identity changes, so opkg owns the added soname without upgrading or
removing QSDK's differently named library. Requires Python 3.9 or later.
"""

import argparse
import gzip
import hashlib
import io
from pathlib import Path
import tarfile
import urllib.request


SOURCE_NAME = "libnl-tiny1_2025.03.19~c0df580a-r1_aarch64_cortex-a53.ipk"
SOURCE_URL = (
    "https://mirrors.pku.edu.cn/immortalwrt/releases/24.10.6/packages/"
    "aarch64_cortex-a53/base/" + SOURCE_NAME
)
SOURCE_SHA256 = "83b615395b2f18cb665ea80a93f2d19ca4ebfa8578ab67ebdae7e67b21a03136"
PACKAGE = "vantage-qwrt-libnl-compat"
VERSION = "2025.03.19-r1"
ARCH = "aarch64_cortex-a53"
LIBRARY = "usr/lib/libnl-tiny.so.1"


def archive(files):
    """Create reproducible root-owned ipk members without filesystem extraction."""
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode="w", format=tarfile.USTAR_FORMAT) as tar:
        for name, data in files.items():
            info = tarfile.TarInfo("./" + name)
            info.size = len(data)
            info.mode = 0o644
            info.uname = info.gname = "root"
            tar.addfile(info, io.BytesIO(data))
    return gzip.compress(out.getvalue(), mtime=0)


def build_package(source):
    if hashlib.sha256(source).hexdigest() != SOURCE_SHA256:
        raise ValueError("source package SHA-256 mismatch")

    with tarfile.open(fileobj=io.BytesIO(source), mode="r:gz") as tar:
        payload = tar.extractfile("./data.tar.gz").read()
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as tar:
        files = [m for m in tar if not m.isdir()]
        if len(files) != 1 or files[0].name.removeprefix("./") != LIBRARY or not files[0].isfile():
            raise ValueError("source package must contain only the versioned compatibility library")
        installed_size = files[0].size

    control = (
        f"Package: {PACKAGE}\nVersion: {VERSION}\nArchitecture: {ARCH}\n"
        "Depends: libc\nSection: libs\nLicense: LGPL-2.1\n"
        f"Installed-Size: {installed_size}\n"
        "Source: https://git.openwrt.org/project/libnl-tiny.git;"
        "c0df580adbd4d555ecc1962dbe88e91d75b67a4e\n"
        "Description: Versioned libnl-tiny for Vantage's rtnl module on QSDK.\n"
        " Leaves QSDK's unversioned libnl-tiny and package registration intact.\n"
    ).encode()
    return archive({
        "debian-binary": b"2.0\n",
        "control.tar.gz": archive({"control": control}),
        "data.tar.gz": payload,
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, help="cached source ipk (same SHA-256 check)")
    parser.add_argument("--out", type=Path, default=Path("dist/qwrt"))
    args = parser.parse_args()
    if args.source:
        source = args.source.read_bytes()
    else:
        with urllib.request.urlopen(SOURCE_URL, timeout=30) as response:
            source = response.read()
    package = build_package(source)
    args.out.mkdir(parents=True, exist_ok=True)
    name = f"{PACKAGE}_{VERSION}_{ARCH}.ipk"
    (args.out / name).write_bytes(package)
    digest = hashlib.sha256(package).hexdigest()
    (args.out / "SHA256SUMS").write_text(f"{digest}  {name}\n")
    print(f"Source SHA-256 verified: {SOURCE_SHA256}")
    print(f"Built {args.out / name}\n{digest}  {name}")


if __name__ == "__main__":
    main()
