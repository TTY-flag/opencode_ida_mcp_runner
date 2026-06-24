import os
import glob
import pathlib
import subprocess

from typing import List
from feeds.core.idahelper import Target
from . import logger


class SigmakeNotFoundException(Exception):
    pass


class SigmakePlatformException(Exception):
    pass


class SigmakePatException(Exception):
    pass


class SigmakeUnknownError(Exception):
    pass


_TARGET_TO_PAT_TOOL = {
    Target.X86_64_PC_WINDOWS_GNU: 'pcf',
    Target.X86_64_PC_WINDOWS_MSVC: 'pcf',
    Target.X86_64_UNKNOWN_LINUX_GNU: 'pelf',
    Target.AARCH64_APPLE_DARWIN: 'pmacho',
}


def target_to_pat_tool(target: Target) -> str:
    tool = _TARGET_TO_PAT_TOOL.get(target)
    if not tool:
        raise SigmakePatException(f'Unsupported target {target}')
    return tool


class Sigmake:
    def __init__(self, flair_bin: pathlib.Path):
        self.flair_bin = flair_bin

    @classmethod
    def create(cls, flair: pathlib.Path) -> 'Sigmake':
        # List all sigmake binaries in the flair directory
        # sigmakes = glob.glob(os.path.join(flair, 'bin', '*', 'sigmake'))
        sigmakes = glob.glob(os.path.join(flair, 'sigmake'))
        if not sigmakes:
            raise SigmakeNotFoundException(f'No sigmake found in {flair}')

        # TODO: detect platform in case we have multiple sigmake binaries
        # if len(sigmakes) > 1:
        #     raise SigmakePlatformException(f'Multiple sigmake binaries found in {flair}')

        return cls(pathlib.Path(sigmakes[0]).parent)

    def pat_tool(self, target: Target) -> pathlib.Path:
        return self.flair_bin / target_to_pat_tool(target)

    def sigmake_tool(self) -> pathlib.Path:
        return self.flair_bin / 'sigmake'

    def zipsig_tool(self) -> pathlib.Path:
        return self.flair_bin / 'zipsig'

    def make_pat(self, target: Target, pat_dest: pathlib.Path, sources: List[pathlib.Path]):
        # Split functions inside sections
        subprocess.check_output([self.pat_tool(target), '-S', *sources, pat_dest])

    def make_sig(self, name: str, sig_dest: pathlib.Path, pat_src: pathlib.Path):
        exc_path = sig_dest.with_suffix('.exc')

        sigmake_cmd = [
            str(self.sigmake_tool()),
            f'-n{name}',
            str(pat_src),
            str(sig_dest),
        ]
        logger.debug(f'Running {sigmake_cmd}')
        cmd = subprocess.run(sigmake_cmd)

        if cmd.returncode != 0:
            # log.info('sigmake failed...')
            resolve_collisions(exc_path)

        # Run again
        try:
            logger.debug(f'Running {sigmake_cmd} a 2nd time')
            subprocess.check_call(sigmake_cmd)
        except subprocess.CalledProcessError as _:
            raise SigmakeUnknownError('sigmake failed a second time')

        logger.info('Running zipsig')
        subprocess.check_call([self.zipsig_tool(), sig_dest])


def resolve_collisions(exc_path: pathlib.Path):
    # TODO: resolve collisions properly

    with open(exc_path, 'r') as f:
        lines = f.readlines()

    with open(exc_path, 'w') as out:
        out.writelines(line for line in lines if not line.startswith(';'))
