#!/usr/bin/env python3
"""Write a validated DPW1 package directly into the mapped assets partition."""

import argparse
import os
import struct
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSET_OFFSET = 0x410000
ASSET_SIZE = 0x3F0000
DEFAULT_PACKAGE = os.path.join(ROOT, "assets", "classic_v05", "animation.dpw")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--port", required=True, help="serial port, for example /dev/cu.usbmodem101"
    )
    parser.add_argument("--package", default=DEFAULT_PACKAGE, help="DPW1 package path")
    parser.add_argument("--baud", type=int, default=460800)
    args = parser.parse_args()

    package = os.path.abspath(args.package)
    if not os.path.isfile(package):
        raise SystemExit("Package not found: %s" % package)
    with open(package, "rb") as stream:
        header = stream.read(18)
    if len(header) != 18 or header[:4] != b"DPW1":
        raise SystemExit("Package must start with a complete DPW1 header")
    version, width, height, count, encoding, flags, total_bytes = struct.unpack_from(
        "<HHHHBBI", header, 4
    )
    actual_bytes = os.path.getsize(package)
    if (
        version != 1
        or width != 240
        or height != 240
        or count < 1
        or count > 360
        or encoding not in (0, 1)
        or total_bytes != actual_bytes
    ):
        raise SystemExit("Invalid DPW1 v1 package header or length")
    if actual_bytes > ASSET_SIZE:
        raise SystemExit(
            "Package is %d bytes; assets partition holds %d bytes"
            % (actual_bytes, ASSET_SIZE)
        )

    core = os.environ.get("PLATFORMIO_CORE_DIR", os.path.join(ROOT, ".pio-core"))
    esptool = os.path.join(core, "packages", "tool-esptoolpy", "esptool.py")
    if not os.path.isfile(esptool):
        raise SystemExit("PlatformIO esptool not found: %s" % esptool)

    command = [
        sys.executable,
        esptool,
        "--chip",
        "esp32s3",
        "--port",
        args.port,
        "--baud",
        str(args.baud),
        "--before",
        "default_reset",
        "--after",
        "hard_reset",
        "write_flash",
        "--flash_size",
        "8MB",
        "--flash_mode",
        "qio",
        "--flash_freq",
        "80m",
        hex(ASSET_OFFSET),
        package,
    ]
    env = os.environ.copy()
    module_path = os.path.join(ROOT, ".tools", "platformio")
    env["PYTHONPATH"] = os.pathsep.join(
        filter(None, [module_path, env.get("PYTHONPATH", "")])
    )
    print(
        "Flashing %d frames, encoding=%s, final_artwork=%s, package=%d/%d bytes"
        % (
            count,
            {0: "RGB565", 1: "JPEG"}[encoding],
            bool(flags & 1),
            actual_bytes,
            ASSET_SIZE,
        )
    )
    subprocess.run(command, check=True, env=env)


if __name__ == "__main__":
    main()
