#!/usr/bin/env python
# -*- coding: UTF8 -*-

# Specto , Unobtrusive event notifier
#
#       balloons.py
#
# Copyright (c) 2005-2007, Jean-François Fortin Tam
# This module code is maintained by : Giulio Lotti

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

import pygtk
pygtk.require('2.0')
import pynotify
import sys

from spectlib import logger
from spectlib.specto_gconf import GConfClient

notifyInitialized = False

class NotificationToast:
    _notifyRealm = 'Specto'
    _Urgencies = {
        'low': pynotify.URGENCY_LOW,
        'critical': pynotify.URGENCY_CRITICAL,
        'normal': pynotify.URGENCY_NORMAL
        }

    # I'd love to have a default icon.
    def __init__(self, specto, body, icon=None, x=0, y=0, urgency="low", summary=_notifyRealm):
        global notifyInitialized

        if not notifyInitialized:
           pynotify.init(self._notifyRealm)
           notifyInitialized = True
        
        self.conf_pref = GConfClient("/apps/specto/preferences")
        self.toast = pynotify.Notification(summary, body)
        self.timeout = self.conf_pref.get_entry("/pop_toast_duration", "integer")*1000
        if self.timeout:
            self.toast.set_timeout(self.timeout)
        self.toast.set_urgency(self._Urgencies[urgency])
        if icon:
            #self.toast.set_property('icon-name', icon)#we now use a pixbuf in the line below to allow themable icons
            self.toast.set_icon_from_pixbuf(icon)
            
        if x!=0 and y!=0:#grab the x and y position of the tray icon and make the balloon emerge from it
            self.toast.set_hint("x", x)
            self.toast.set_hint("y", y)
        
        if not self.toast.show():
            specto.logger.log("Can't send Notification message. Check your DBUS!", "error", self.__class__)
