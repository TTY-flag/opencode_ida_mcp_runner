import pathlib
import traceback
from typing import Dict, Any
from collections import defaultdict

from feeds.core.idahelper import Target, IDA
from feeds.rust import git
from PyQt5.QtCore import QRunnable, pyqtSlot, pyqtSignal, QObject
from . import logger

dependencies_loaded = True
failed_dependency = []
try:
    from feeds.rust import sigmake, rust
except ImportError as e:
    dependencies_loaded = False
    failed_dependency.append(e.name)


def get_rust_info(binary: pathlib.Path) -> Dict[str, Any]:
    info = defaultdict(str, {
        'target': IDA.guess_target(),
        'hash': rust.guess_rustc_hash(binary),
    })
    info['version'] = git.commit_to_tag(info['hash'])
    logger.debug(f'rust info: {info}')
    return info


def process(info: {}, flair: pathlib.Path) -> pathlib.Path:
    maker = sigmake.Sigmake.create(flair)

    assert info['target'] != ''

    return rust.make_signature(
        maker,
        info,
    )

class SigmakeWorkerSignals(QObject):
    # Result sig
    done = pyqtSignal(pathlib.Path)
    # Error
    error = pyqtSignal(str)
    # Progress message
    message = pyqtSignal(str)


class SigmakeWorker(QRunnable):
    def __init__(self, info: {}, flair_path: pathlib.Path):
        super().__init__()
        self.flair_path = flair_path
        self.info = info
        self.emitter = SigmakeWorkerSignals()

    pyqtSlot()
    def run(self):
        if dependencies_loaded:
            self.emitter.message.emit('Creating signature, please wait...')
            try:
                sig_path = process(self.info, self.flair_path)
                self.emitter.message.emit(f'Signature created: {sig_path}')
                self.emitter.done.emit(sig_path)
            except Exception as _:
                self.emitter.message.emit('Failed to create signature')
                self.emitter.error.emit(traceback.format_exc())
        else:
            self.emitter.error.emit(f'Missing dependencies {failed_dependency}, please install the required libraries from requirements.txt')
