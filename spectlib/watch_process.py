#!/usr/bin/env python
# -*- coding: UTF8 -*-

# Specto , Unobtrusive event notifier
#
#       watch_process.py
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

from spectlib.watch import Watch
from spectlib.i18n import _
from spectlib.process import ProcessList

import thread
import gtk, time
import os

class Process_watch(Watch):
    """ 
    Watch class that will check if a file was modified, removed or created. 
    """
    updated = False
    type = 3
    
    def __init__(self, refresh, process, specto, id,  name = _("Unknown Process Watch")):
        Watch.__init__(self, specto)
        self.name = name
        self.refresh = refresh
        self.process = process
        self.id = id
        self.error = False
        self.actually_updated=False
        self.running = self.check_process()

    def dict_values(self):
        return { 'name': self.name, 'refresh': self.refresh, 'process': self.process, 'type':3 }
       
    def start_watch(self):
        """ Start the watch. """
        self.thread_update()
        
    def thread_update(self):
        lock = thread.allocate_lock()
        lock.acquire()
        t=thread.start_new_thread(self.update,(lock,))
        while lock.locked():
            while gtk.events_pending():
                gtk.main_iteration()
            time.sleep(0.05)
        while gtk.events_pending():
            gtk.main_iteration()  
                
    def update(self, lock):
        """ See if a file was modified or created. """
        self.error = False
        self.specto.mark_watch_busy(True, self.id)
        self.specto.logger.log(_("Updating watch: \"%s\"") % self.name, "info", self.__class__)
        
        try:
            process = self.check_process()
            if self.running and process == False:
                self.running = False
                self.updated = True
                self.actually_updated = True
            elif self.running == False and process == True:
                self.running = True 
                self.actually_updated = True
            else: self.actually_updated=False
        except:
            self.error = True
            self.specto.logger.log(_("Watch: \"%s\" has an error") % self.name, "error", self.__class__)
        
        self.specto.mark_watch_busy(False, self.id)
        Watch.update(self, lock)
        
    def check_process(self):
        """ see if the process is running or not """
        p = ProcessList()
        pid = p.named(self.process)
        if pid:
            return True
        else:
            return False
        
    def set_process(self, process):
        self.process = process
