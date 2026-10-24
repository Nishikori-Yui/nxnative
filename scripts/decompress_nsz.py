#!/usr/bin/env python3
"""Decompress NSZ files to standard NSP containers.

The NSZ tool verifies the NCA hashes while writing the NSP. The source files
are never removed by this wrapper.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def nsz_executable():
    """Find the nsz CLI in the active environment or on PATH."""
    candidates = []
    if os.environ.get("NSZ_BIN"):
        candidates.append(Path(os.environ["NSZ_BIN"]).expanduser())
    found = shutil.which("nsz")
    if found:
        candidates.append(Path(found))
    candidates.append(Path(sys.executable).with_name("nsz"))
    candidates.append(Path(sys.prefix) / "bin" / "nsz")
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    return None


def output_name(source):
    """Return the NSP name produced by nsz for an NSZ input."""
    return source.with_suffix(".nsp").name


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Losslessly decompress NSZ files to standard NSP files."
    )
    parser.add_argument(
        "files",
        nargs="+",
        type=Path,
        help="one or more .nsz files",
    )
    parser.add_argument(
        "-k",
        "--keys",
        required=True,
        type=Path,
        help="path to prod.keys",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        help="directory for the NSP files (default: <first file>/decompressed)",
    )
    parser.add_argument(
        "-w",
        "--overwrite",
        action="store_true",
        help="allow nsz to replace existing NSP files",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    keys = args.keys.expanduser().resolve()
    if not keys.is_file():
        print(f"error: prod.keys does not exist: {keys}", file=sys.stderr)
        return 2

    sources = [p.expanduser().resolve() for p in args.files]
    missing = [p for p in sources if not p.is_file()]
    if missing:
        for path in missing:
            print(f"error: NSZ file does not exist: {path}", file=sys.stderr)
        return 2
    invalid = [p for p in sources if p.suffix.lower() != ".nsz"]
    if invalid:
        for path in invalid:
            print(f"error: expected an .nsz file: {path}", file=sys.stderr)
        return 2

    output_dir = (
        args.output_dir.expanduser().resolve()
        if args.output_dir
        else sources[0].parent / "decompressed"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    nsz = nsz_executable()
    if nsz is None:
        print(
            "error: the nsz CLI was not found. Install it in the active Python "
            "environment with: python3 -m pip install nsz",
            file=sys.stderr,
        )
        return 2

    command = [str(nsz), "-D", "--keys", str(keys), "-o", str(output_dir)]
    if args.overwrite:
        command.append("-w")
    command.extend(str(path) for path in sources)

    result = subprocess.run(command)
    if result.returncode != 0:
        return result.returncode

    outputs = [output_dir / output_name(path) for path in sources]
    missing_outputs = [path for path in outputs if not path.is_file()]
    if missing_outputs:
        for path in missing_outputs:
            print(f"error: nsz did not create the expected NSP: {path}", file=sys.stderr)
        return 1

    print(f"decompressed {len(outputs)} NSZ file(s) into {output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
