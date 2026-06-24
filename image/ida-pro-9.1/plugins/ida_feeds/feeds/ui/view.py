import os
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QProgressBar, QSplitter, \
    QAbstractItemView, QMenu, QAction, QHBoxLayout, \
    QTreeView, QWidget, QVBoxLayout, QPushButton, QSizePolicy, QHeaderView, \
    QLineEdit, QMessageBox, QLabel, QDialog, QComboBox, QToolButton, QStyle, QGroupBox, QFrame, QStatusBar
from feeds.ui.filter import CustomFilterProxyModel
from feeds.ui.model import FolderModel, SignatureItemState


class FolderView(QTreeView):
    def __init__(self):
        super().__init__()
        self.model = FolderModel()
        self.model.setHorizontalHeaderLabels(['Folder'])
        self.setModel(self.model)
        self.setColumnWidth(0, 250)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QAbstractItemView.SingleSelection)


class FoldersPanel(QWidget):
    def __init__(self, parent=None):
        super(FoldersPanel, self).__init__(parent)

        self.layout = QVBoxLayout()
        self.folders = FolderView()
        self.button_open = QPushButton("Open signatures folder")
        self.button_open.setDefault(True)
        self.layout.addWidget(self.button_open)
        self.layout.addWidget(self.folders)
        self.setLayout(self.layout)


class SignaturesControls(QWidget):
    def __init__(self, parent=None):
        super(SignaturesControls, self).__init__(parent)

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.button_probe = QPushButton("Run probe")
        self.button_apply = QPushButton("Apply signatures")
        self.button_probe.setDisabled(True)
        self.button_apply.setDisabled(True)

        self.filter = QLineEdit()
        self.filter.setMinimumWidth(150)
        self.filter.setPlaceholderText("Filter by regex")

        self.probe_setting = QComboBox()
        self.probe_help_text = ("<b>Parallel probing</b> distributes signature probing across multiple processes. "
                                "Requires RPyC 5.x, <b>idapro</b> python module and <b>idalib</b>. "
                                "Uses a lot more disk space as each process runs on a copy of the opened IDB.<br><br>"
                                "<b>Sequential probing</b> is slower, has no dependencies and runs on the "
                                "opened IDB in the main thread.")
        self.probe_setting.setToolTip(self.probe_help_text)
        self.probe_help = QToolButton()
        self.probe_help.setIcon(self.style().standardIcon(QStyle.SP_TitleBarContextHelpButton))
        self.probe_help.setToolTip(self.probe_help_text)

        self.layout.addWidget(self.filter)
        self.layout.addWidget(self.probe_setting)
        self.layout.addWidget(self.button_probe)
        self.layout.addWidget(self.button_apply)
        self.layout.setStretchFactor(self.filter, 600)
        self.layout.setStretchFactor(self.probe_setting, 100)
        self.layout.setStretchFactor(self.button_probe, 100)
        self.layout.setStretchFactor(self.button_apply, 100)
        self.setLayout(self.layout)

class SignaturesPanel(QWidget):
    def __init__(self, parent=None):
        super(SignaturesPanel, self).__init__(parent)

        self.layout = QVBoxLayout()
        self.signatures = SignaturesView()
        self.center_label = QLabel('No valid signature found. Click \"Open signatures folder\" to import signatures.')
        self.center_label.setAlignment(Qt.AlignCenter)
        self.center_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.controls = SignaturesControls()
        self.layout.addWidget(self.controls)
        self.layout.addWidget(self.signatures)
        self.layout.addWidget(self.center_label)
        self.setLayout(self.layout)
        self.show_empty()

    def show_empty(self, yes: bool = True):
        if yes:
            # self.filter.hide()
            self.controls.hide()
            self.signatures.hide()
            self.center_label.show()
        else:
            # self.filter.show()
            self.controls.show()
            self.signatures.show()
            self.center_label.hide()


class ActionsPanel(QWidget):
    def __init__(self, parent=None):
        super(ActionsPanel, self).__init__(parent)

        self.button_probe = QPushButton("Run probe")
        self.button_apply = QPushButton("Apply signatures")
        self.button_probe.setDisabled(True)
        self.button_apply.setDisabled(True)

        self.probe_setting = QComboBox()
        self.probe_help_text = ("<b>Parallel probing</b> distributes signature probing across multiple processes. "
                                "Requires RPyC 5.x, <b>idapro</b> python module and <b>idalib</b>. "
                                "Uses a lot more disk space as each process runs on a copy of the opened IDB.<br><br>"
                                "<b>Sequential probing</b> is slower, has no dependencies and runs on the "
                                "opened IDB in the main thread.")
        self.probe_setting.setToolTip(self.probe_help_text)
        self.probe_help = QToolButton()
        self.probe_help.setIcon(self.style().standardIcon(QStyle.SP_TitleBarContextHelpButton))
        self.probe_help.setToolTip(self.probe_help_text)

        self.layout = QHBoxLayout()
        self.layout.addStretch()
        # self.layout.addWidget(self.probe_help)
        self.layout.addWidget(self.probe_setting)
        self.layout.addWidget(self.button_probe)
        self.layout.addWidget(self.button_apply)
        self.layout.addStretch()
        self.layout.setStretch(0, 2)
        self.layout.setStretch(1, 1)
        self.layout.setStretch(2, 1)
        self.layout.setStretch(3, 1)
        self.layout.setStretch(4, 2)
        # self.layout.setStretch(5, 2)
        self.setLayout(self.layout)


class WaitDialog(QMessageBox):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Loading binary")
        self.setText("Auto-analysis in progress, please wait...")
        self.setStandardButtons(QMessageBox.NoButton)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setModal(True)
        self.setAttribute(Qt.WA_DeleteOnClose)


class ProgressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Progress")
        self.setFixedSize(300, 150)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.setWindowFlag(Qt.WindowMinimizeButtonHint, False)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)

        # Layout
        layout = QVBoxLayout(self)

        # Label
        self.label = QLabel("Processing, please wait...")
        layout.addWidget(self.label)

        # Progress Bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)

    def accept(self):
        self.close()
        self.label.setText("Processing, please wait...")


class SignaturesView(QTreeView):
    def __init__(self):
        super().__init__()
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setAlternatingRowColors(False)

        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['File', 'Library name', '# Matches', 'State'])
        self.model.setHeaderData(0, Qt.Horizontal, "Signature file name", Qt.ToolTipRole)
        self.model.setHeaderData(1, Qt.Horizontal, "Library name extracted from signature file", Qt.ToolTipRole)
        self.model.setHeaderData(2, Qt.Horizontal, "For 'Probed' state - estimated number of matches"
                                                   "\nFor 'Applied' state - actual number of matches"
                                                   "\n\tNOTE: When applying multiple sigs, applying order affects the actual number of matches.",
                                 Qt.ToolTipRole)
        self.model.setHeaderData(3, Qt.Horizontal, "State of the file: None, Probed or Applied", Qt.ToolTipRole)

        self.proxy_model = CustomFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.setModel(self.proxy_model)

        # Set the header resize mode
        self.header = self.header()
        self.header.setSectionResizeMode(QHeaderView.Interactive)
        self.header.resizeSections(QHeaderView.ResizeToContents)
        # Enable custom context menu
        self.context_menu = QMenu(self)
        # self.open_action = QAction("Open signatures folder", self)
        self.analysis_action = QAction("Run parallel probing", self)
        self.apply_action = QAction("Apply signatures", self)
        self.hide_no_matches_action = QAction("Hide no matches", self)
        self.hide_no_matches_action.setCheckable(True)

        self.undo_action = None
        self.redo_action = None
        self.undo_shortcut = None
        self.redo_shortcut = None

        self.expand_all_action = QAction("Expand all", self)
        self.collapse_all_action = QAction("Collapse all", self)
        self.cancel_action = QAction("Close", self)
        # self.context_menu.addAction(self.open_action)
        self.context_menu.addAction(self.hide_no_matches_action)
        self.context_menu.addSeparator()
        self.context_menu.addAction(self.analysis_action)
        self.context_menu.addAction(self.apply_action)
        self.context_menu.addSeparator()
        self.context_menu.addAction(self.expand_all_action)
        self.context_menu.addAction(self.collapse_all_action)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setSortingEnabled(True)


    def add_row(self, root, file_path, name, matches, state: SignatureItemState = SignatureItemState.NONE):
        columns = []

        head, tail = os.path.split(os.path.relpath(file_path, root))
        if head != '':
            item = QStandardItem(f'{tail} ({head})')
        else:
            item = QStandardItem(f'{tail}')
        item.setData(file_path, Qt.UserRole)
        columns.append(item)

        item = QStandardItem(name)
        columns.append(item)

        item = QStandardItem(matches)
        if matches > -1:
            item.setData(matches, Qt.UserRole)
            item.setText(str(matches))
        else:
            item.setData(-1, Qt.UserRole)
            item.setText('')
        columns.append(item)

        item = QStandardItem(state.description)
        item.setData(state.value_int, Qt.UserRole)
        columns.append(item)

        for item in columns:
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        self.model.appendRow(columns)
        self.set_row_list_state(columns, state)

    def set_row_list_state(self, row: [], row_state: SignatureItemState = SignatureItemState.NONE):
        for item in row:
            self.set_row_state(item, row_state)

    def set_row_state(self, row, row_state: SignatureItemState = SignatureItemState.NONE):
        cols = self.model.columnCount()
        for col in range(cols):
            item = self.get_item_from_source(row, col)
            self.set_item_state(item, row_state)

    def set_item_state(self, item, row_state: SignatureItemState = SignatureItemState.NONE):
        font = item.font()
        if row_state == SignatureItemState.VERIFIED:
            font.setItalic(True)
            font.setBold(False)
            item.setFont(font)
        elif row_state == SignatureItemState.APPLIED:
            font.setItalic(False)
            font.setBold(True)
            item.setFont(font)
        else:
            font.setItalic(False)
            font.setBold(False)
            item.setFont(font)

    def get_item_from_source(self, index, column):
        row = index.row()
        item_index = self.model.index(row, column)
        return self.model.itemFromIndex(item_index)

class RustPanel(QWidget):
    def __init__(self):
        super(RustPanel, self).__init__()

        self.layout = QVBoxLayout()
        self.button = QPushButton("Create and apply signature")
        self.button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.description = "Press the \"Generate Rust Signature\" button when you're ready to proceed."
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setText(self.description)

        self.layout.addStretch()
        self.layout.addWidget(self.label, alignment=Qt.AlignCenter)
        self.layout.addWidget(self.button, alignment=Qt.AlignCenter)
        self.layout.addStretch()
        self.setLayout(self.layout)

class FeedsView(QWidget):
    def __init__(self):
        super(FeedsView, self).__init__()

        self.layout = QVBoxLayout()
        self.splitter = QSplitter()
        self.wait_dialog = WaitDialog()
        self.progress_dialog = ProgressDialog(parent=self)

        self.download_label = QLabel(
            'Download more signatures packs from <a href="https://my.hex-rays.io">my.hex-rays.com</a>')
        palette = self.download_label.palette()
        palette.setColor(QPalette.WindowText, palette.color(QPalette.Link))
        self.download_label.setPalette(palette)
        self.download_label.setAlignment(Qt.AlignCenter)
        self.download_label.setOpenExternalLinks(True)
        self.download_label.setDisabled(True)
        self.download_label.hide()

        self.panel_folders = FoldersPanel()
        self.panel_user_signatures = SignaturesPanel()
        self.panel_rust_generator = RustPanel()
        self.panel_rust_signatures = SignaturesPanel()

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.splitter.addWidget(self.panel_folders)
        self.splitter.addWidget(self.panel_user_signatures)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 2)

        self.layout.addWidget(self.splitter)

        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
        self.progress_bar = QProgressBar()
        self.layout.addWidget(self.status_label)
        self.layout.addWidget(self.progress_bar)
        self.progress_bar.hide()
        self.status_label.hide()

    def set_visible(self, panel):
        if self.splitter.indexOf(panel) == -1:
            self.splitter.replaceWidget(1, panel)
            self.splitter.setStretchFactor(1, 2)
