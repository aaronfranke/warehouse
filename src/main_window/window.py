# window.py
#
# Copyright 2023 Heliguy
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License only.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-only

import os
import pathlib
import subprocess
import re
import time

from gi.repository import Adw, Gdk, Gio, GLib, Gtk
from .packages_page import PackagesPage
from .const import Config

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/main_window/window.ui")
class WarehouseWindow(Adw.ApplicationWindow):
    __gtype_name__ = "WarehouseWindow"
    gtc = Gtk.Template.Child
    main_breakpoint = gtc()
    main_split = gtc()
    sidebar_button = gtc()

    def key_handler(self, controller, keyval, keycode, state):
        if keyval == Gdk.KEY_w and state == Gdk.ModifierType.CONTROL_MASK:
            self.close()
        if keyval == Gdk.KEY_Escape:
            self.batch_mode_button.set_active(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Extra Object Creation
        self.settings = Gio.Settings.new("io.github.flattool.Warehouse")
        event_controller = Gtk.EventControllerKey()
        file_drop = Gtk.DropTarget.new(Gio.File, Gdk.DragAction.COPY)

        # Apply
        self.settings.bind("window-width", self, "default-width", Gio.SettingsBindFlags.DEFAULT)
        self.settings.bind("window-height", self, "default-height", Gio.SettingsBindFlags.DEFAULT)
        self.settings.bind("is-maximized", self, "maximized", Gio.SettingsBindFlags.DEFAULT)
        self.settings.bind("is-fullscreen", self, "fullscreened", Gio.SettingsBindFlags.DEFAULT)
        self.add_controller(event_controller)
        # self.scrolled_window.add_controller(file_drop)
        self.main_split.set_content(PackagesPage(self))
        if Config.DEVEL:
            self.add_css_class("devel")

        # Connections
        event_controller.connect("key-pressed", self.key_handler)
        # file_drop.connect("drop", self.drop_callback)
        self.sidebar_button.connect("clicked", lambda *_: self.main_split.set_show_sidebar(False))