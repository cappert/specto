#!/usr/bin/env python
# -*- coding: UTF8 -*-

# Specto , Unobtrusive event notifier
#
#       watch_mail_imap.py
#
# Copyright (c) 2005-2007, Jean-François Fortin Tam
# This module code is maintained by : Wout Clymans and Jean-François Fortin Tam

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

from spectlib.gmailatom import GmailAtom
import os
from spectlib.i18n import _
import thread
import gtk, time

class Mail_watch(Watch):
    """
    this watch will check if you have a new mail on your gmail account
    """
    updated = False
    oldMsg = 0
    newMsg = 0
    type = 1
    prot = 2 #gmail protocol
    
    def __init__(self, refresh, username, password, specto, id,  name = _("Unknown Mail Watch")):
        Watch.__init__(self, specto)
        self.name = name
        self.refresh = refresh
        if "@gmail.com" not in username:
            self.user = username + "@gmail.com"
        else:
            self.user = username
        self.password = password
        self.id = id
        self.error = False
        
    def dict_values(self):
        return { 'name': self.name, 'refresh': self.refresh, 'username': self.user, 'password':self.password, 'type':1, 'prot':2 }
        
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
        """ Check for new mails on your gmail account. """
        self.error = False
        self.specto.update_watch(True, self.id)
        self.specto.logger.log(_("Updating watch: \"%s\"") % self.name, "info", self.__class__)
        
        try:
            s = GmailAtom(self.user, self.password)
            s.refreshInfo()
            self.newMsg = s.getUnreadMsgCount()
            if not self.oldMsg: self.oldMsg = 0
            if self.updated==False:#if the watch has been cleared, make the message count will be right next time we check
                self.oldMsg=0
            if self.newMsg == 0:#no unread messages, we need to clear the watch
                self.oldMsg = 0
                self.specto.notifier.clear_watch("", self.id)
            elif self.newMsg > self.oldMsg:
                self.updated = True
            elif self.oldMsg==self.newMsg:
                pass #no new unread messages.
            elif self.oldMsg > self.newMsg:#the unread mail count went down! That means the user most likely deleted some of them, so we have to adjust our count.
                self.oldMsg = self.newMsg
        except:
            self.error = True
            self.specto.logger.log(_("Watch: \"%s\" has error: wrong username/password") % self.name, "error", self.__class__)
            
        self.specto.update_watch(False, self.id)
        lock.release()
        Watch.update(self)
        
    def set_username(self, username):
        """ Set the username for the watch. """
        self.user = username
        
    def set_password(self, password):
        """ Set the password for the watch. """
        self.password = password
