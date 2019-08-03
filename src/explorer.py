from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QComboBox, QMenu
from dwarf.ui.widgets.list_view import DwarfListView


class Explorer(QWidget):

    def __init__(self, plugin):
        super().__init__()

        self.plugin = plugin
        self.adb = plugin.adb

        self.current_path = ''

        self.path_input = QComboBox(self)
        self.path_input.activated[str].connect(self.set_path)

        self.explorer = DwarfListView()
        self.explorer_model = QStandardItemModel(0, 6)
        self.explorer_model.setHeaderData(0, Qt.Horizontal, 'permissions')
        self.explorer_model.setHeaderData(1, Qt.Horizontal, 'uid')
        self.explorer_model.setHeaderData(2, Qt.Horizontal, 'gid')
        self.explorer_model.setHeaderData(3, Qt.Horizontal, 'size')
        self.explorer_model.setHeaderData(4, Qt.Horizontal, 'modified')
        self.explorer_model.setHeaderData(5, Qt.Horizontal, 'name')
        self.explorer.setModel(self.explorer_model)
        self.explorer.doubleClicked.connect(self._item_double_clicked)
        self.explorer.setContextMenuPolicy(Qt.CustomContextMenu)
        self.explorer.customContextMenuRequested.connect(self._on_context_menu)

        box = QVBoxLayout()
        box.addWidget(self.path_input)
        box.addWidget(self.explorer)
        self.setLayout(box)

    def set_path(self, path):
        if self.current_path == path:
            return

        self.current_path = path

        ls = self.adb.su_cmd('ls -al %s' % path)
        if ls and ls[:2] != 'ls':
            ls = ls.split('\n')[1:]

            self.path_input.clear()
            self.explorer_model.setRowCount(0)

            split = path.split('/')
            self.path_input.addItem(path)
            for i in range(1, len(split)):
                path = '/'.join(split[:-i])
                if path:
                    self.path_input.addItem(path)

            for line in ls:
                if line:
                    parts = line.split()
                    self.explorer_model.appendRow([
                        QStandardItem(parts[0]),
                        QStandardItem(parts[2]),
                        QStandardItem(parts[3]),
                        QStandardItem(parts[4]),
                        QStandardItem('%s %s' % (parts[5], parts[6])),
                        QStandardItem(parts[7]),
                    ])

    def _item_double_clicked(self, model_index):
        row = self.explorer_model.itemFromIndex(model_index).row()
        if row != -1:
            name = self.explorer_model.item(row, 5).text()
            if name == '..':
                path = '/'.join(self.current_path.split('/')[:-1])
            else:
                path = self.current_path + '/' + name

            ret = self.adb.su_cmd('cd %s' % path)
            if not ret:
                self.set_path(path)

    def _on_context_menu(self, pos):
        row = self.explorer.indexAt(pos).row()
        glbl_pt = self.explorer.mapToGlobal(pos)
        if row != -1:
            context_menu = QMenu(self)
            name = self.explorer_model.item(row, 5).text()
            context_menu.addAction('pull file', lambda: self._on_pull_file(name))
            context_menu.exec_(glbl_pt)

    def _on_pull_file(self, name):
        from PyQt5.QtWidgets import QFileDialog
        _file = QFileDialog.getSaveFileName(self.plugin.app, '', name)
        if _file[0]:
            path = self.current_path + '/' + name if self.current_path != '/' else self.current_path + name
            dwarf_temp = '/sdcard/.dwarf_temp'
            self.adb.su_cmd('cp -r %s %s' % (path, dwarf_temp))
            self.adb.pull(dwarf_temp, _file[0])
            self.adb.su_cmd('rm -rf %s' % dwarf_temp)
