#!/usr/bin/env python
#
# Copyright (c) Facebook, Inc. and its affiliates.
#
# List of environment variables used:
#
#  NLE_BUILD_RELEASE
#    If set, builds wheel (s)dist such as to prepare it for upload to PyPI.
#
#  HACKDIR
#    If set, install NetHack's data files in this directory.
#
import os
import pathlib
import shutil
import subprocess
import sys
import sysconfig

import setuptools
from setuptools.command import build_ext


class CMakeBuild(build_ext.build_ext):
    def run(self):  # Necessary for pip install -e.
        for ext in self.extensions:
            self.build_extension(ext)

    def build_extension(self, ext):
        source_path = pathlib.Path(__file__).parent.resolve()
        output_path = (
            pathlib.Path(self.get_ext_fullpath(ext.name))
            .parent.joinpath("nle")
            .resolve()
        )
        hackdir_path = os.getenv("HACKDIR", output_path.joinpath("nethackdir"))

        os.makedirs(self.build_temp, exist_ok=True)
        build_type = "Debug" if self.debug else "Release"

        generator = "Ninja" if shutil.which("ninja") else "Unix Makefiles"

        cmake_cmd = [
            "cmake",
            str(source_path),
            "-G%s" % generator,
            "-DPYTHON_SRC_PARENT=%s" % source_path,
            # Tell cmake which Python we want.
            "-DPYTHON_EXECUTABLE=%s" % sys.executable,
            "-DCMAKE_BUILD_TYPE=%s" % build_type,
            "-DCMAKE_INSTALL_PREFIX=%s" % sys.base_prefix,
            "-DCMAKE_LIBRARY_OUTPUT_DIRECTORY=%s" % output_path,
            "-DHACKDIR=%s" % hackdir_path,
            "-DPYTHON_INCLUDE_DIR=%s" % sysconfig.get_paths()["include"],
            "-DPYTHON_LIBRARY=%s" % sysconfig.get_config_var("LIBDIR"),
        ]

        build_cmd = ["cmake", "--build", ".", "--parallel"]
        install_cmd = ["cmake", "--install", "."]

        try:
            subprocess.check_call(cmake_cmd, cwd=self.build_temp)
            subprocess.check_call(build_cmd, cwd=self.build_temp)
            # Installs nethackdir. TODO: Can't we do this with setuptools?
            subprocess.check_call(install_cmd, cwd=self.build_temp)
        except subprocess.CalledProcessError:
            # Don't obscure the error with a setuptools backtrace.
            sys.exit(1)


if __name__ == "__main__":
    cwd = os.path.dirname(os.path.abspath(__file__))
    version = open("version.txt", "r").read().strip()
    sha = "Unknown"

    try:
        sha = (
            subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=cwd)
            .decode("ascii")
            .strip()
        )
    except subprocess.CalledProcessError:
        pass

    if sha != "Unknown" and not os.getenv("NLE_RELEASE_BUILD"):
        version += "+" + sha[:7]
    package_name = setuptools.find_packages()[0]
    print("Building wheel {}-{}".format(package_name, version))

    version_path = os.path.join(cwd, "nle", "version.py")
    with open(version_path, "w") as f:
        f.write("__version__ = '{}'\n".format(version))
        f.write("git_version = {}\n".format(repr(sha)))

    setuptools.setup(
        version=version,
        ext_modules=[setuptools.Extension("nle", sources=[])],
        cmdclass={"build_ext": CMakeBuild},
        classifiers=[
            "License :: OSI Approved :: Nethack General Public License",
            "Development Status :: 5 - Production/Stable",
            "Operating System :: POSIX :: Linux",
            "Operating System :: MacOS",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: 3.11",
            "Programming Language :: Python :: 3.12",
            "Programming Language :: Python :: 3.13",
            "Programming Language :: C",
            "Programming Language :: C++",
            "Topic :: Scientific/Engineering :: Artificial Intelligence",
            "Topic :: Games/Entertainment",
        ],
        zip_safe=False,
    )
