"""
Dwarf - Copyright (C) 2019 Giovanni Rocca (iGio90)

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>
"""
import os

from PyQt5.QtCore import QObject, Qt
from PyQt5.QtGui import QStandardItemModel
from dwarf.ui.widgets.list_view import DwarfListView

from drdwarf.src.explorer import Explorer


class Plugin(QObject):

    @staticmethod
    def __get_plugin_info__():
        return {
            'name': 'drdwarf',
            'description': 'Android extension for Dwarf',
            'version': '1.0.0',
            'author': 'iGio90',
            'homepage': 'https://github.com/iGio90/drdwarf',
            'license': 'https://www.gnu.org/licenses/gpl-3.0',
        }

    def __init__(self, app):
        super().__init__()
        self.app = app

        self.adb = None
        self.explorer = None

        self.app.session_manager.sessionCreated.connect(self._on_session_created)

    def _on_session_created(self):
        if self.app.session_manager.session.session_type == 'android':
            self.adb = self.app.session_manager.session.adb

            if self.adb._is_root:
                self.app.panels_menu.addSeparator()
                self.app.panels_menu.addAction('Android explorer', self.create_widget)

    def create_widget(self):
        if self.explorer is None:
            self.explorer = Explorer(self)

            data_path = self.adb.get_data_path_for_package(self.app.dwarf.package)
            if len(data_path) > 0 and data_path.startswith('package:'):
                parts = data_path.split('/')[:-1]
                try:
                    parts[3] = parts[3][:parts[3].index('-')]
                except:
                    pass
                data_path = '/'.join(parts)[8:].replace('/data/app', '/data/data')
            self.explorer.set_path(data_path)

        self.app.main_tabs.addTab(self.explorer, 'Android explorer')
        self.app.main_tabs.setCurrentIndex(self.app.main_tabs.indexOf(self.explorer))
