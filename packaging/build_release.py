"""Build the release artifacts: the onedir bundle, a portable ZIP, an installer.

Run from the repository root:

    python packaging/build_release.py            # everything available
    python packaging/build_release.py --no-installer

Produces, under dist/:
    Coinductor/                       the PyInstaller onedir bundle
    Coinductor-<version>-portable.zip unzip-and-run, no installer needed
    installer/Coinductor-<version>-setup.exe
    SHA256SUMS.txt                    checksums for every shipped file

The checksums matter more than usual here: the binaries are unsigned, so
SmartScreen will warn on first run and a published hash is the only way for
someone to tell a real download from a tampered one.
"""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
BUNDLE = DIST / "Coinductor"

ISCC_CANDIDATES = (
    Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Inno Setup 6" / "ISCC.exe",
    Path(os.environ.get("ProgramFiles(x86)", "")) / "Inno Setup 6" / "ISCC.exe",
    Path(os.environ.get("ProgramFiles", "")) / "Inno Setup 6" / "ISCC.exe",
)


def version() -> str:
    sys.path.insert(0, str(ROOT))
    import trading_agent

    return trading_agent.__version__


def run(command: list[str], what: str) -> None:
    print(f"\n=== {what} ===", flush=True)
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode != 0:
        raise SystemExit(f"{what} failed with exit code {result.returncode}")


def build_bundle() -> None:
    shutil.rmtree(ROOT / "build", ignore_errors=True)
    shutil.rmtree(BUNDLE, ignore_errors=True)
    run(
        [sys.executable, "-m", "PyInstaller", "--noconfirm",
         "--distpath", "dist", "--workpath", "build",
         str(ROOT / "packaging" / "coinductor.spec")],
        "PyInstaller bundle",
    )
    exe = BUNDLE / "Coinductor.exe"
    if not exe.exists():
        raise SystemExit(f"expected {exe} to exist after the build")


def build_portable_zip() -> Path:
    target = DIST / f"Coinductor-{version()}-portable.zip"
    target.unlink(missing_ok=True)
    print(f"\n=== portable ZIP -> {target.name} ===", flush=True)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(BUNDLE.rglob("*")):
            if path.is_file():
                # Keep a top-level Coinductor/ folder so unzipping never
                # scatters 3000 files into the user's Downloads.
                archive.write(path, Path("Coinductor") / path.relative_to(BUNDLE))
    return target


def build_installer() -> Path | None:
    iscc = next((path for path in ISCC_CANDIDATES if path.is_file()), None)
    if iscc is None:
        print("\n=== installer skipped: Inno Setup 6 (ISCC.exe) not found ===")
        return None
    run([str(iscc), str(ROOT / "packaging" / "coinductor.iss")], "Inno Setup installer")
    produced = DIST / "installer" / f"Coinductor-{version()}-setup.exe"
    return produced if produced.exists() else None


def write_checksums(paths: list[Path]) -> Path:
    target = DIST / "SHA256SUMS.txt"
    lines = []
    for path in paths:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        lines.append(f"{digest.hexdigest()}  {path.name}")
        print(f"  {digest.hexdigest()}  {path.name}")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-installer", action="store_true", help="skip the Inno Setup step")
    parser.add_argument("--skip-build", action="store_true", help="reuse an existing dist/Coinductor")
    args = parser.parse_args()

    if not args.skip_build:
        build_bundle()
    elif not BUNDLE.exists():
        raise SystemExit(f"--skip-build needs an existing {BUNDLE}")

    artifacts = [build_portable_zip()]
    if not args.no_installer:
        installer = build_installer()
        if installer is not None:
            artifacts.append(installer)

    print("\n=== SHA256SUMS.txt ===", flush=True)
    write_checksums(artifacts)

    print(f"\nCoinductor {version()} release artifacts are in {DIST}")
    for path in artifacts:
        print(f"  {path.relative_to(ROOT)}  ({path.stat().st_size / 1_048_576:.0f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
