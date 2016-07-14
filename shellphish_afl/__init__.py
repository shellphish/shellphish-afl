import os
import distutils

def afl_bin(platform):
    return os.path.join(afl_dir(platform), 'afl-fuzz')

def afl_path_var(platform):
    if platform == 'cgc':
        return os.path.join(afl_dir(platform), 'tracers/i386')
    elif platform == 'multi-cgc': # fakeforksrv is in the same dir
        return afl_dir(platform)
    else:
        return os.path.join(afl_dir(platform), 'tracers', platform)

def afl_dir(platform):
    if platform == 'cgc':
        d = 'afl-cgc'
    elif platform == 'multi-cgc':
        d = os.path.join('afl-multi-cgc', 'afl')
    else:
        d = 'afl-unix'
    return os.path.join(_all_base(), d)

def _all_base():
    if __file__.startswith(distutils.sysconfig.PREFIX):
        return os.path.join(distutils.sysconfig.PREFIX, 'bin')
    else:
        return os.path.join(os.path.dirname(__file__), '..', 'bin')
