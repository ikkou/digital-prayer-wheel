"""Work around the GC9A01 ID byte order returned by M5Dial v1.1 panels."""

Import("env")

from pathlib import Path


libdeps = Path(env.subst("$PROJECT_LIBDEPS_DIR")) / env.subst("$PIOENV")
source = libdeps / "M5GFX" / "src" / "M5GFX.cpp"
if not source.is_file():
    raise RuntimeError(
        "M5GFX.cpp is missing; install the configured M5Dial dependencies first"
    )

text = source.read_text(encoding="utf-8")
stock_check = "if ((id & 0xFFFFFF) == 0x019a00)"
patched_check = "if ((id & 0xFFFFFF) == 0x019a00 || (id & 0xFFFF) == 0x019A)"

if patched_check not in text:
    if stock_check not in text:
        raise RuntimeError(
            "Unrecognized M5GFX GC9A01 probe; review before changing the patch"
        )
    source.write_text(text.replace(stock_check, patched_check, 1), encoding="utf-8")
    print("M5Dial v1.1 GC9A01 ID compatibility: patched M5GFX autodetection")
