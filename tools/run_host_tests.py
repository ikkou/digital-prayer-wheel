#!/usr/bin/env python3
"""Compile and run the hardware-independent model checks with the host C++ compiler."""

import os
import shlex
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    compiler = shlex.split(os.environ.get("CXX", "clang++"))
    test_binary = os.path.join(tempfile.gettempdir(), "digital-prayer-wheel-host-tests")
    command = compiler + [
        "-std=c++11",
        "-Wall",
        "-Wextra",
        "-Werror",
        "-I",
        os.path.join(ROOT, "include"),
        os.path.join(ROOT, "tests", "host", "test_models.cpp"),
        os.path.join(ROOT, "src", "RotationModel.cpp"),
        "-o",
        test_binary,
    ]
    subprocess.run(command, cwd=ROOT, check=True)
    subprocess.run([test_binary], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
