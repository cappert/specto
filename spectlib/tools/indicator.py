# -*- coding: utf-8 -*-

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
import dbus
import signal
import re

class Process(object):
    """Represents a process"""

    def __init__(self, pid):
        """Make a new Process object"""
        self.proc = "/proc/%d" % pid
        self.proc_stat_file = file(os.path.join(self.proc, "stat")).read()
        
        """
        Here's how we split the values in the stat file with a regex.
        This is to prevent a very rare, corner-case bug in Specto. When you have a running process whose name contains spaces, its mere presence will prevent Specto from launching at all. The reason is that we used a naive approach to splitting (splitting with spaces).

        A normal stat file looks somewhat like this:
            19217 (some_script ) S 17776 19217

        However, it can look like this, if the process name has spaces:
            19217 (some script ) S 17776 19217

        To split this properly, we need to use this regex:
            \([^()]*\)|\S+

        Which can be decomposed as:
            \(      = the "(" character
            [^()]*  = a serie of zero or more characters, except "(" or ")"
            \)      = the ")" character
            |       = OR operator
            \S+     = match at least 1 character that is not a "space" (blank space, \t, \n, etc.)

        So, it looks like this:
            re.findall(r'\([^()]*\)|\S+', the_string_to_parse)

        Or, in a more readable way (with "re.X" to remove the whitespaces in the regex):
            re.findall(r' \( [^()]* \) | \S+ ', the_string_to_parse, re.X)
        """
        
        pid, command, state, parent_pid = re.findall(r' \( [^()]* \) | \S+ ', self.proc_stat_file, re.X)[:4]  # Only keep the first 4 items
        command = command[1:-1]  # Remove the surrounding "(" and ")"
        self.pid = int(pid)
        self.command = command  # FIXME process names are truncated in the stat file. Not sure what we can do about this, other than truncate our own process names in the "named" function near (see further below).
        self.state = state
        self.parent_pid = int(parent_pid)
        self.parent = None
        self.children = []

    def kill(self, sig = signal.SIGTERM):
        """Kill this process with SIGTERM by default"""
        os.kill(self.pid, sig)

    def __repr__(self):
        return "Process(pid = %r)" % self.pid

    def getcwd(self):
        """Read the current directory of this process or None for can't"""
        try:
            return os.readlink(os.path.join(self.proc, "cwd"))
        except OSError:
            return None


class ProcessList(object):
    """Represents a list of processes"""

    def __init__(self):
        """Read /proc and fill up the process lists"""
        self.by_pid = {}
        self.by_command = {}
        for f in os.listdir("/proc"):
            if f.isdigit():
                process = Process(int(f))
                self.by_pid[process.pid] = process
                self.by_command.setdefault(process.command, []).append(process)
        for process in self.by_pid.values():
            try:
                parent = self.by_pid[process.parent_pid]
                parent.children.append(process)
                process.parent = parent
            except KeyError:
                pass

    def named(self, name):
        """Returns a list of processes with the given name"""
        name = name[:15]#FIXME: this is a hack around the bug found a few lines ago, not a real solution
        return self.by_command.get(name, [])  


def check_indicator_running():
    p = ProcessList()
    pid = p.named("indicator-applet")
    if not pid:
        raise Exception('Indicator applet not running')

check_indicator_running()

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
        if icon:
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