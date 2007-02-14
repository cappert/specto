#!/usr/bin/env python
# -*- coding: UTF8 -*-

# Specto , Unobtrusive event notifier
#
#       watch_port.py
#
# Copyright (c) 2005-2007, Jean-François Fortin Tam
# This module code is maintained by : Thomas McColgan

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

import thread
import gtk, time
import os

class Port_watch(Watch):
    """ 
    Watch class that will check if a connection was established on a certain port 
    """
    updated = False
    type = 4
    
    def __init__(self, refresh, port, specto, id,  name = _("Unknown Process Watch")):
        Watch.__init__(self, specto)
        self.name = name
        self.refresh = refresh
        self.port = port
        self.id = id
        self.error = False
        self.actually_updated=False
        self.running = self.check_port()

    def dict_values(self):
        return { 'name': self.name, 'refresh': self.refresh, 'port': self.port, 'type':4 }
       
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
            established = self.check_port()
            if self.running and established == False:
                self.running = False
                self.updated = True
                self.actually_updated = True
            elif self.running == False and established == True:
                self.running = True 
                self.actually_updated = True
            else: self.actually_updated=False
        except:
            self.error = True
            self.specto.logger.log(_("Watch: \"%s\" has an error") % self.name, "error", self.__class__)
        
        self.specto.mark_watch_busy(False, self.id)
        Watch.update(self, lock)
        
    def check_port(self):
        """ see if there is a connection on the port or not """
        conn = False
        y=os.popen( 'netstat -nt','r').read().splitlines()
        del y[0]
        del y[0]
	for k in y:
	    k = k.split(' ')
	    while True:
	        try:
	            k.remove('')
	        except:
	            break
            if int(k[3].split(':')[1]) == int(self.port):
	        conn = True

	if conn:
            return True
        else:
            return False
        
    def set_port(self, port):
        self.port = port
