import os
import shutil
import subprocess
from distutils.errors import LibError
from distutils.core import setup
from distutils.command.build import build as _build
from setuptools.command.develop import develop as _develop

AFL_UNIX_INSTALL_PATH = os.path.join("bin", "afl-unix")
AFL_UNIX_PATCH_FILE = os.path.join("patches", "afl-patch.diff")
BUILD_QEMU_PATCH_FILE = os.path.join("patches", "build_qemu.diff")
AFL_UNIX_GEN = os.path.join(os.curdir, "patches", "build.sh")
AFL_CGC_INSTALL_PATH = os.path.join("bin", "afl-cgc")
AFL_MULTI_CGC_INSTALL_PATH = os.path.join("bin", "afl-multi-cgc")
SUPPORTED_ARCHES = ["aarch64", "x86_64", "i386", "arm", "ppc", "ppc64", "mips", "mipsel", "mips64"]
QEMU_PATCHES = ["patches/memfd.diff", "patches/gettid.diff", "patches/syscall_sockios.diff", "patches/stime.diff"]
MULTIARCH_LIBRARY_PATH = os.path.join("bin", "fuzzer-libs")
AFL_QEMU_MODE_PATCH = AFL_UNIX_INSTALL_PATH+"/qemu_mode/patches/"
AFL_UNIX_FUZZ = os.path.join(AFL_UNIX_INSTALL_PATH)
AFL_CGC_FUZZ  = os.path.join(AFL_CGC_INSTALL_PATH)
AFL_MULTI_CGC_FUZZ  = os.path.join(AFL_MULTI_CGC_INSTALL_PATH)


def _setup_other_arch():
    # revisiting the afl mirrorer repo
    if not os.path.exists(AFL_UNIX_INSTALL_PATH):
        AFL_UNIX_REPO = "https://github.com/mirrorer/afl"
        if subprocess.call(['git', 'clone','--depth=1', AFL_UNIX_REPO, AFL_UNIX_INSTALL_PATH]) != 0:
            raise LibError("Unable to retrieve afl-unix")

        with open(BUILD_QEMU_PATCH_FILE, "rb") as f:
            if subprocess.check_call(['patch', '-p0'],stdin=f, cwd=AFL_UNIX_INSTALL_PATH) != 0:
                raise LibError("Unable to apply patches to qemu build")

        if subprocess.call(['cp',AFL_UNIX_GEN, AFL_UNIX_INSTALL_PATH]) != 0:
            raise LibError("Build file doesn't exist")

        # patches for QEMU to work with ubuntu 18.04 and above
        if subprocess.check_call(['cp'] + QEMU_PATCHES + [AFL_QEMU_MODE_PATCH]) != 0:
            raise LibError('Patches to make QEMU work with Ubuntu 18.04 and above not found')

        if subprocess.check_call(['./build.sh'] + SUPPORTED_ARCHES, cwd=AFL_UNIX_INSTALL_PATH) != 0:
            raise LibError("Unable to build afl-other-arch")

def _setup_cgc():

    if not os.path.exists(AFL_CGC_INSTALL_PATH):
        AFL_CGC_REPO = "https://github.com/shellphish/driller-afl.git"
        if subprocess.call(['git', 'clone', AFL_CGC_REPO, AFL_CGC_INSTALL_PATH]) != 0:
            raise LibError("Unable to retrieve afl-cgc")

        if subprocess.call(['make', '-j'], cwd=AFL_CGC_INSTALL_PATH) != 0:
            raise LibError("Unable to make afl-cgc")

        if subprocess.call(['./build_qemu_support.sh'], cwd=os.path.join(AFL_CGC_INSTALL_PATH, "qemu_mode")) != 0:
            raise LibError("Unable to build afl-cgc-qemu")

    if not os.path.exists(AFL_MULTI_CGC_INSTALL_PATH):
        AFL_MULTI_CGC_REPO = "https://github.com/mechaphish/multiafl.git"
        if subprocess.call(['git', 'clone', AFL_MULTI_CGC_REPO, AFL_MULTI_CGC_INSTALL_PATH]) != 0:
            raise LibError("Unable to retrieve afl-multi-cgc")

        if subprocess.call(['make', '-j'], cwd=AFL_MULTI_CGC_INSTALL_PATH) != 0:
            raise LibError("Unable to make afl-multi-cgc")

def _setup_libs():
    if not os.path.exists(MULTIARCH_LIBRARY_PATH):
        if subprocess.call(["./fetchlibs.sh"], cwd=".") != 0:
            raise LibError("Unable to fetch libraries")

data_files = [ ]
def _datafiles():
    # for each lib export it into data_files
    for path,_,files in os.walk("bin/fuzzer-libs"):
        libs = [ os.path.join(path, f) for f in files if '.so' in f ]
        if libs:
            data_files.append((path, libs))

    # grab all the executables from afl
    for s in ('afl-multi-cgc', 'afl-cgc', 'afl-unix'):
        for path,_,files in os.walk(os.path.join("bin", s)):
            if 'qemu-2.' in path:
                continue
            paths = [ os.path.join(path, f) for f in files ]
            exes = [ f for f in paths if os.path.isfile(f) and os.access(f, os.X_OK) ]
            if exes:
                data_files.append((path, exes))

    return data_files

def get_patches():
    # get all patches
    for path,_,files in os.walk("patches"):
        patches = [os.path.join(path, f) for f in files]
        if patches:
            data_files.append((path, patches))

    return data_files

class build(_build):
    def run(self):
        self.execute(_setup_other_arch, (), msg="Setting up AFL-other-arch")
        self.execute(_setup_cgc, (), msg="Setting up AFL-cgc")
        self.execute(_setup_libs, (), msg="Getting libraries")
        _datafiles()
        _build.run(self)

class develop(_develop):
    def run(self):
        self.execute(_setup_other_arch, (), msg="Setting up AFL-other-arch")
        self.execute(_setup_cgc, (), msg="Setting up AFL-cgc")
        self.execute(_setup_libs, (), msg="Getting libraries")
        _datafiles()
        _develop.run(self)

get_patches()

setup(
    name='shellphish-afl', version='1.2.2', description="pip package for afl",
    packages=['shellphish_afl'],
    cmdclass={'build': build, 'develop': develop},
    data_files=data_files,
    scripts=['fetchlibs.sh'],
)
