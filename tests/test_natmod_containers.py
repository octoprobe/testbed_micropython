"""
git clone --depth=1 --branch=v0.32 https://github.com/eliben/pyelftools.git /tmp/pylibs/pyelftools
git clone --depth=1 --branch=v1.0.0 https://github.com/vidstige/ar.git /tmp/pylibs/ar
PYTHONPATH=/tmp/pyelftools


"""

import dataclasses
import pathlib
import shutil
import subprocess
import textwrap

# run-natmodtests.py
TEST_MAPPINGS = {
    "btree": "btree/btree_$(ARCH).mpy",
    # "deflate": "deflate/deflate_$(ARCH).mpy",
    # "framebuf": "framebuf/framebuf_$(ARCH).mpy",
    # "heapq": "heapq/heapq_$(ARCH).mpy",
    # "random": "random/random_$(ARCH).mpy",
    # "re": "re/re_$(ARCH).mpy",
}

# EXAMPLES = ["examples/natmod/heapq"]
EXAMPLES = [f"examples/natmod/{k}" for k in TEST_MAPPINGS.keys()]

DIRECTORY_MICROPYTHON = pathlib.Path("/home/maerki/gits/micropython")
assert DIRECTORY_MICROPYTHON.is_dir()

DIRECTORY_PYLIBS = pathlib.Path("/tmp/pylibs")
assert DIRECTORY_PYLIBS.is_dir()
PYLIBS = ["pyelftools", "ar"]
for pylib in PYLIBS:
    assert (DIRECTORY_PYLIBS / pylib).is_dir()


@dataclasses.dataclass(frozen=True)
class Arch:
    arch: str
    container: str
    extra_args: str = ""
    pyelftools_patch: bool = True


# ARM_BUILD_CONTAINER = "micropython/build-micropython-arm"
# BUILD_CONTAINERS = {
#     "stm32": ARM_BUILD_CONTAINER,
#     "rp2": ARM_BUILD_CONTAINER,
#     "nrf": ARM_BUILD_CONTAINER,
#     "mimxrt": ARM_BUILD_CONTAINER,
#     "renesas-ra": ARM_BUILD_CONTAINER,
#     "samd": ARM_BUILD_CONTAINER,
#     "psoc6": "ifxmakers/mpy-mtb-ci",
#     "esp32": "espressif/idf:v5.4.1",
#     "esp8266": "larsks/esp-open-sdk",
#     "unix": "gcc:12-bookworm",  # Special, doesn't have boards
# }

# x86, x64, armv7m, xtensa, xtensawin, rv32imc
# armv5te, armv6, armv6m, armv7-a, armv7m, rv32imac, rv32imc, rv32i, xtensa

# /build/mpy-cross --help
# x86, x64, armv6, armv6m, armv7m, armv7em, armv7emsp, armv7emdp, xtensa, xtensawin, rv32imc, host, debug

# py/dynruntime.mk
ARCHS = [
    Arch(
        arch="armv6m",
        container="micropython/build-micropython-arm",
    ),
    Arch(
        arch="armv7m",
        container="micropython/build-micropython-arm",
    ),
    Arch(
        arch="armv7emdp",
        container="micropython/build-micropython-arm",
    ),
    Arch(
        arch="rv32imc",
        container="micropython/build-micropython-rp2350riscv",
        extra_args="CROSS=riscv32-unknown-elf-",
        pyelftools_patch=True,
    ),
    Arch(
        arch="xtensa",
        container="larsks/esp-open-sdk",
        pyelftools_patch=True,
    ),
    Arch(
        arch="xtensawin",
        container="espressif/idf:v5.4.1",
        pyelftools_patch=True,
    ),
]


def main() -> None:
    failed: list[Arch] = []
    for arch in ARCHS:
        for example in EXAMPLES:
            args_ext: list[str] = []
            opt_ext = ""
            if arch.pyelftools_patch:
                args_ext = [
                    f"--volume={DIRECTORY_PYLIBS}:{DIRECTORY_PYLIBS}",
                    f"--env=PYTHONPATH={DIRECTORY_PYLIBS}/pyelftools:{DIRECTORY_PYLIBS}/ar",
                ]
            args = [
                "/usr/bin/docker",
                "run",
                "--rm",
                f"--volume={DIRECTORY_MICROPYTHON}:{DIRECTORY_MICROPYTHON}",
                *args_ext,
                "--user=1000:1000",
                arch.container,
                "bash",
                "-c",
                f"{opt_ext} make -C {DIRECTORY_MICROPYTHON}/{example} ARCH={arch.arch} {arch.extra_args}",
            ]
            rc = subprocess.run(
                args=args,
                cwd=DIRECTORY_MICROPYTHON,
                text=True,
                shell=False,
                capture_output=True,
            )
            print(f"{rc.returncode}: {arch.arch} {example}")
            print(f"    {' '.join(args)}")
            if rc.stdout is not None:
                print(textwrap.indent(rc.stdout, "    "))
            if rc.stderr is not None:
                print(textwrap.indent(rc.stderr, "    "))
            if rc.returncode != 0:
                failed.append(arch)

            shutil.rmtree(DIRECTORY_MICROPYTHON / example / "build", ignore_errors=True)

    print(f"Failed: {[a.arch for a in failed]}")


if __name__ == "__main__":
    main()
