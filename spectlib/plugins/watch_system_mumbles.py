# -*- coding: utf-8 -*-

# Specto , Unobtrusive event notifier
#
#       watch_system_mumbles.py
#
# See the AUTHORS file for copyright ownership information

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
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

from spectlib.watch import Watch
import spectlib.config
import spectlib.gtkconfig
from spectlib.i18n import _
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop

type = "Watch_system_mumbles"
type_desc = _("Mumbles")
icon = 'mumbles'
category = _("System")
dbus_watch = True

MUMBLES_DBUS_NAME = 'org.mumblesproject.Mumbles'
MUMBLES_DBUS_OBJECT = '/org/mumblesproject/Mumbles'
MUMBLES_DBUS_INTERFACE = 'org.mumblesproject.Mumbles'

class MumblesDBus(dbus.service.Object):
    def __init__(self):
        dbus_loop = DBusGMainLoop()
        bus_name = dbus.service.BusName(MUMBLES_DBUS_NAME, dbus.SessionBus(mainloop=dbus_loop))
        dbus.service.Object.__init__(self, bus_name, MUMBLES_DBUS_OBJECT)

    @dbus.service.method(dbus_interface=MUMBLES_DBUS_INTERFACE, in_signature='ss') 
    def Notify(self, title, message):
        self._Notify(title, message)
    
    @dbus.service.signal(dbus_interface=MUMBLES_DBUS_INTERFACE, signature='ss')     
    def _Notify(self, title, message):
        pass
        
def check_instance():
    bus = dbus.SessionBus()
    obj = bus.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus')
    iface = dbus.Interface(obj, 'org.freedesktop.DBus')
    if not MUMBLES_DBUS_NAME in iface.ListNames():
        mumbles = MumblesDBus()             
        

def get_add_gui_info():
    return []


class Watch_system_mumbles(Watch):
    """
    Watch class that will check mumbles messages send with mumbles-send.
    """

    def __init__(self, specto, id, values):

        watch_values = []
        check_instance()

        self.icon = icon
        self.standard_open_command = ''
        self.type_desc = type_desc

        #Init the superclass and set some specto values
        Watch.__init__(self, specto, id, values, watch_values)
        
        self.dbus = True
        self.message = ""
        self.extra_info = ""
        # Use the dbus interface we saw in dbus-notify
        self.dbus_interface = MUMBLES_DBUS_INTERFACE
        self.dbus_path = MUMBLES_DBUS_OBJECT
        self.dbus_name = MUMBLES_DBUS_NAME

        self.signals = {"_Notify": self.notify}
        
        
    def notify(self, subject, content):
        self.message = subject
        self.extra_info = content
        self.watch_changed()
    
    def get_balloon_text(self):
        """ create the text for the balloon """
        return self.message + "\n\n" + self.extra_info

    def get_extra_information(self):
        return self.message + "\n\n" + self.extra_info

    def get_gui_info(self):
        return [(_('Name'), self.name),
                (_('Last changed'), self.last_changed)]
