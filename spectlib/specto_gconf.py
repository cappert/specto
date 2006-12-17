#!/usr/bin/env python
# -*- coding: UTF8 -*-

# Specto , Unobtrusive event notifier
#
#       specto_gconf.py
#
# Copyright (c) 2005, Jean-François Fortin Tam
# This module code is maintained by : Conor Callahan, Jean-François Fortin,Pascal Potvin and Wout Clymans

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

import gconf

class GConfClient:
    """
    Specto gconf class. 
    """
    
    def __init__(self, directory):
        # Get the GConf object
        self.client = gconf.client_get_default()
        self.client.add_dir (directory, gconf.CLIENT_PRELOAD_NONE)
        self.directory = directory

    def get_entry(self, key, type_):
        """ Returns the value of a key. """
        k = self.directory + key
        s = ""

        if type_ == "string":
            s = self.client.get_string(k)
        elif type_ == "boolean":
            s = self.client.get_bool(k)
        elif type_ == "integer":
            s = self.client.get_int(k)
        elif type_ == "float":
            s = self.client.get_float(k)
                
        return s

    def set_entry(self, key, entry, type_):
        """ Set the value from a key. """
        k = self.directory + key

        if type_ == "boolean":
            self.client.set_bool(k, entry)
        elif type_ == "string":
            self.client.set_string(k, entry)
        elif type_ == "integer":
            self.client.set_int(k, entry)
        elif type_ == "float":
            self.client.set_float(k, entry)

    def unset_entry(self,key):
        """ Unset (remove) the key. """
        self.client.unset(self.directory + key)
        
    def notify_entry(self, key, callback, label):
        """ Listen for changes in a key. """
        self.client.notify_add (self.directory + key, callback, label)
