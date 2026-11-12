"""Create or verify the reproducible SHA-256 manifest for a frozen Day 2 set."""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "SHA256SUMS.csv"
FIELDS = ("path", "sha256", "bytes")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def payload_files() -> list[Path]:
    """Return every frozen payload file, excluding the manifest itself."""
    return sorted(
        (path for path in ROOT.rglob("*") if path.is_file() and path != MANIFEST),
        key=lambda path: path.relative_to(ROOT).as_posix(),
    )


def create() -> int:
    files = payload_files()
    with MANIFEST.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        for path in files:
            writer.writerow(
                {
                    "path": path.relative_to(ROOT).as_posix(),
                    "sha256": sha256(path),
                    "bytes": path.stat().st_size,
                }
            )
    print(f"Created {MANIFEST.name} for {len(files)} frozen files.")
    return 0


def verify() -> int:
    if not MANIFEST.is_file():
        print(f"FAIL: {MANIFEST.name} is missing.")
        return 1

    with MANIFEST.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if tuple(reader.fieldnames or ()) != FIELDS:
            print(f"FAIL: {MANIFEST.name} must have columns: {', '.join(FIELDS)}.")
            return 1
        rows = list(reader)

    listed: dict[str, dict[str, str]] = {}
    for row in rows:
        relative = row["path"]
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts:
            print(f"FAIL: unsafe path in manifest: {relative!r}.")
            return 1
        if relative in listed:
            print(f"FAIL: duplicate path in manifest: {relative}.")
            return 1
        listed[relative] = row

    actual_files = {path.relative_to(ROOT).as_posix(): path for path in payload_files()}
    if set(listed) != set(actual_files):
        missing = sorted(set(actual_files) - set(listed))
        extra = sorted(set(listed) - set(actual_files))
        print(f"FAIL: file set mismatch; unlisted={missing}, missing_files={extra}.")
        return 1

    for relative, path in actual_files.items():
        row = listed[relative]
        if int(row["bytes"]) != path.stat().st_size:
            print(f"FAIL: size mismatch for {relative}.")
            return 1
        if row["sha256"] != sha256(path):
            print(f"FAIL: SHA-256 mismatch for {relative}.")
            return 1

    print(f"PASS: verified {len(actual_files)} frozen files against {MANIFEST.name}.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--create", action="store_true", help="write a sorted SHA-256 manifest")
    action.add_argument("--verify", action="store_true", help="verify hashes, sizes and exact file set")
    args = parser.parse_args()
    return create() if args.create else verify()


if __name__ == "__main__":
    raise SystemExit(main())
