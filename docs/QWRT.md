# Vantage for QWRT

This is the maintained QWRT fork of
[anothaDev/luci-theme-vantage](https://github.com/anothaDev/luci-theme-vantage).
The theme, dashboard, translations and compatibility changes all live in
[one repository](https://github.com/Demogorgon314/luci-theme-vantage).
No fork of LuCI, rpcd, ucode or libnl is required for these changes.

## Releases and compatibility

Download packages from this fork's
[Releases](https://github.com/Demogorgon314/luci-theme-vantage/releases).
The first release is `v1.0.12-qwrt.1`, with package version `1.0.12-r2`,
based on upstream v1.0.12. Upstream v1.0.13 has not been integrated into
this tested release baseline. The `qwrt` development branch now integrates
upstream v1.0.13 as `1.0.13-r2`, with port traffic totals and swconfig switch
details. That development code is not part of the `v1.0.12-qwrt.1` tag.

Runtime checks covered a QWRT QSDK 12.5 ARM64 image with QCA wireless
drivers, modern LuCI/ucode, and opkg. Its advertised firmware version does
not determine its package format: use IPK with opkg and APK with apk.
Other firmware images need their own runtime checks. These packages do
not replace firmware drivers or native system libraries.

The QWRT changes provide QCA runtime interface mappings, Wi-Fi 7 mode
normalization, storage meters and bridge-learned hosts. On legacy libnl
images, bridge discovery avoids the native module that could crash rpcd
and invalidate login sessions. This path does not report VLAN IDs.

## Install from release files (opkg)

Download these four assets and `SHA256SUMS-24.10`:

- `luci-theme-vantage_1.0.12-r2_all.ipk`
- `luci-app-vantage_1.0.12-r2_all.ipk`
- `luci-i18n-vantage-theme-zh-cn_1.0.12-r2_all.ipk`
- `luci-i18n-vantage-zh-cn_1.0.12-r2_all.ipk`

Verify the files on your computer, then copy them to your router. The
address below is a documentation placeholder.

```sh
sha256sum -c --ignore-missing SHA256SUMS-24.10
scp -O luci-*.ipk root@192.0.2.1:/tmp/
```

On the router:

```sh
opkg install /tmp/luci-theme-vantage_1.0.12-r2_all.ipk /tmp/luci-app-vantage_1.0.12-r2_all.ipk /tmp/luci-i18n-vantage-theme-zh-cn_1.0.12-r2_all.ipk /tmp/luci-i18n-vantage-zh-cn_1.0.12-r2_all.ipk
```

If you previously installed the temporary `vantage-qwrt-libnl-compat`
package, remove it with `opkg remove vantage-qwrt-libnl-compat`. It is no
longer needed. Then reload rpcd, log in again and force-refresh the page:

```sh
/etc/init.d/rpcd reload
```

Choose Vantage under System → System → Language and Style if it is not
already selected. The dashboard's Storage section is inside the System
tile. Its read ACL adds only `luci.getMountPoints`; no new write access is
granted by that release. The later v1.0.13 integration also includes
upstream's read-only `luci.getSwconfigPortState` grant. Firmware updates may
require reinstalling these packages.

## Signed update feeds

This fork's feed is published at
[Demogorgon314.github.io/luci-theme-vantage](https://Demogorgon314.github.io/luci-theme-vantage/).
Use this fork's feed instead of the upstream Vantage feed for these
package names; an upstream upgrade can replace the QWRT adaptations.
Keep your firmware's normal dependency feeds.

For opkg, verify the public key before adding it:

```sh
wget -O /tmp/qwrt-24.10.usign.pub https://Demogorgon314.github.io/luci-theme-vantage/qwrt-24.10.usign.pub
usign -F -p /tmp/qwrt-24.10.usign.pub
# must print 36f38cc55cf41341
opkg-key add /tmp/qwrt-24.10.usign.pub
echo 'src/gz vantage_qwrt https://Demogorgon314.github.io/luci-theme-vantage/24.10' >> /etc/opkg/customfeeds.conf
opkg update
opkg install luci-theme-vantage luci-app-vantage luci-i18n-vantage-theme-zh-cn luci-i18n-vantage-zh-cn
```

Later upgrades use `opkg update` and `opkg upgrade` with those four package
names. Do not add the same feed line more than once.

For apk, use `keys/qwrt-signing.pem` from this repository, with SHA-256
`3dbdd86c2b8f6e343d5fa947affc5bb229fb82e1f1c949c5f28b2614355df54d`.
The signed index is at
`https://Demogorgon314.github.io/luci-theme-vantage/25.12/packages.adb`.
The upstream keys retained under `keys/` do not sign this fork's releases.

## Maintaining the fork

- Keep adaptations on the `qwrt` branch. The existing `main` branch keeps
  the upstream history; merge reviewed upstream release commits into
  `qwrt`, resolving and testing compatibility changes there.
- Keep both package versions/releases equal. Increment `PKG_RELEASE` for
  fork fixes on the same upstream version, and update this guide's file
  names and the changelog for a release.
- Push `qwrt` and wait for CI tests and both SDK builds. Download the two
  artifacts and combine their `SHA256SUMS` files into
  `.release-manifests/<tag>.sha256`. Commit the manifest, then push a
  `v<upstream-version>-qwrt.<revision>` tag. The tag pipeline rebuilds,
  verifies the committed hashes, signs the indexes and publishes the
  release and Pages feed. A tag alone without a matching manifest fails.
- The `release-signing` environment holds `VANTAGE_SIGN_KEY` (EC PEM) and
  `VANTAGE_USIGN_KEY` (usign). Their public keys must match the QWRT files
  in `keys/`. Keep private backups outside the repository. Never commit
  private keys or reuse upstream maintainer keys.
- Run the checks in `AGENTS.md`. Runtime verification must exercise the
  full dashboard poll, including CPU, mounts, bridge hosts and host hints,
  with the same session and rpcd process surviving repeated requests.
  Offline unit tests cannot prove native library compatibility.

For rollback, reinstall the four packages from the previous QWRT release,
reload rpcd and log in again. Preserve `/etc/config/vantage` if you want
to retain device aliases. All general uninstall and theme-switching steps
remain in [INSTALL.md](INSTALL.md).
