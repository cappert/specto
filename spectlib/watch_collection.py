#!/usr/bin/env python
# -*- coding: UTF8 -*-

# Specto , Unobtrusive event notifier
#
#       watch_collection.py
#
# Copyright (c) 2005-2007, Jean-François Fortin Tam
# This module code is maintained by : Wout Clymans

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
import os, sys

class Watch_collection:
    def __init__(self):
        self.watch_db = []
        self.id = 0
        self.plugin_dict = {}
        self.load_plugins()
                
    def load_plugins(self):
        dir = "spectlib/plugins/"
        for f in os.listdir(dir):
            if f[-3:] == ".py":
                _file = dir + f[:-3]
                mod = __import__(_file)
                obj = sys.modules[_file]
                self.plugin_dict[obj.type] = mod        
                
    def add(self,specto, values):
        """ read the content from the dictionary and create the watch """        
        for i in values:
            type = values[i]['type']
            
            #get the right object and create the watch object
            obj = getattr(self.plugin_dict[type], type)
            watch_ = obj(specto, self.id, values[i])
            
            self.watch_db.append(watch_)
            self.id+=1
        
    def remove(self, id):
        """ remove the watch from the collection """
        self.watch_db[id].stop()
        self.watch_db[id].updated = False        
        del self.watch_db[id]
        
    def get(self, id):
        """ get a watch object """
        return self.watch_db[id]
    
    def clear_all_watches(self):
        """ mark all watches as not updated """
        for watch in self.watch_db:
            watch.clear()
        
    def start_all_watches(self):
        """ start all watches in the collection """
        for watch in self.watch_db:
            watch.start()
        
    def stop_all_watches(self):
        """ stop all watches in the collection """
        for watch in self.watch_db:
            watch.stop()
        
    def restart_all_watches(self):
        """ restart all watches in the collection """
        for watch in self.watch_db:
            watch.restart()
        
    def length(self):
        """ return the length from the collection """
        return len(self.watch_db)
    
    def count_updated_watches(self):
        """ Count the number of updated watches for the tooltip. """
        count_updates = {}
        for watch in self.watch_db:
            try:
                count_updates[watch.type]
            except:
                count_updates[watch.type] = 0
            
            if watch.updated == True:
                count_updates[watch.type] += 1
                
        return count_updates
    
    def __getitem__(self, i):
        return self.watch_db[i]
