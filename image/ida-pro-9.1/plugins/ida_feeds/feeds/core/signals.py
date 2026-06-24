from PyQt5.QtCore import pyqtSignal, QObject


class WorkerSignals(QObject):
    start = pyqtSignal(int)
    finish = pyqtSignal()
    error = pyqtSignal(object)
    result = pyqtSignal(object, object)
    update = pyqtSignal(int)

probe_signals = WorkerSignals()

class UISignals(QObject):
    filter_path = pyqtSignal(object)
    refresh = pyqtSignal(bool)
    process_finished = pyqtSignal()

ui_signals = UISignals()
