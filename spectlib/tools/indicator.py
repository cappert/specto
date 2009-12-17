# -*- coding: UTF8 -*-

# Specto , Unobtrusive event notifier
#
#       indicator.py
#
# See the AUTHORS file for copyright ownership information

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with this program; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

import indicate
import os
import sys
import time

PROGRAM_NAME = "specto"
LAUNCH_DIR = os.path.abspath(sys.path[0])
DATA_DIRS = [LAUNCH_DIR]

try:
    import xdg.BaseDirectory
    DATA_BASE_DIRS = xdg.BaseDirectory.xdg_data_dirs
    CACHE_BASE_DIR = xdg.BaseDirectory.xdg_cache_home
except ImportError:
    DATA_BASE_DIRS = [
            os.path.join(os.path.expanduser("~"), ".local", "share"),
            "/usr/local/share", "/usr/share"]
    CACHE_BASE_DIR = os.path.join(os.path.expanduser("~"), ".cache")

DATA_DIRS += [os.path.join(d, PROGRAM_NAME) for d in DATA_BASE_DIRS]

class Indicator:
    def __init__(self, specto):
        self.specto = specto
        self.indicate_srv = indicate.indicate_server_ref_default()
        self.indicate_srv.set_type("message.%s" % PROGRAM_NAME)
        self.indicate_srv.set_desktop_file(self.get_desktop_file())
        self.indicate_srv.connect("server-display", self.specto.toggle_notifier)
        self.indicate_srv.show()
        self.indicate_db = {}
        
    def add_indicator(self, watch):
        icon = self.specto.notifier.get_icon(watch.icon, 0, False)
        try:
            # Ubuntu 9.10 and above
            _indicator = indicate.Indicator()
        except:
            # Ubuntu 9.04
            _indicator = indicate.IndicatorMessage()
        _indicator.set_property("subtype", "im")
        _indicator.set_property("sender", watch.name)
        _indicator.set_property("body", watch.get_balloon_text())
        _indicator.set_property_time("time", time.time())
        _indicator.set_property_icon("icon", icon)
        _indicator.set_property('draw-attention', 'true')
        _indicator.connect("user-display", watch.open_watch)
        _indicator.show()
        
        
        self.indicate_db.update({watch.id: _indicator})
        
    def remove_indicator(self, id):
        if self.indicate_db.has_key(id):
            del self.indicate_db[id]
        
    def get_desktop_file(self):
        dt = "%s.desktop" % PROGRAM_NAME
        p = os.path.join(LAUNCH_DIR, dt)
        if os.path.exists(p):
            return p
        for base in DATA_BASE_DIRS:
            p = os.path.join(base, "applications", dt)
            if os.path.exists(p):
                return p        