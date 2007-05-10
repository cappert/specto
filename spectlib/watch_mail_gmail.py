# -*- coding: UTF8 -*-

# Specto , Unobtrusive event notifier
#
#       watch_mail_gmail.py
#
# Copyright (c) 2005-2007, Jean-François Fortin Tam

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
    actually_updated = False
    oldMsg = 0
    newMsg = 0
    type = 1
    prot = 2 #gmail protocol
    mail_info = []
    
    def __init__(self, refresh, username, password, specto, id,  name = _("Unknown Mail Watch")):
        Watch.__init__(self, specto)
        self.name = name
        self.refresh = refresh
        if "@" not in username:
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
        
    def _real_update(self):
        lock = thread.allocate_lock()
        lock.acquire()
        t=thread.start_new_thread(self.update,(lock,))
        while lock.locked():
            while gtk.events_pending():
                gtk.main_iteration()
            time.sleep(0.05)
        while gtk.events_pending():
            gtk.main_iteration()
        
    def thread_update(self):
        if not self.specto.connection_manager.connected():
            self.specto.logger.log(_("No network connection detected"),
                                   "info", self.__class__)
            self.specto.connection_manager.add_callback(self._real_update)
            self.specto.mark_watch_busy(False, self.id)
        else :
            self._real_update()
        
    def update(self, lock):
        """ Check for new mails on your gmail account. """
        self.error = False
        self.specto.mark_watch_busy(True, self.id)
        self.specto.logger.log(_("Updating watch: \"%s\"") % self.name, "info", self.__class__)
        
        try:
            s = GmailAtom(self.user, self.password)
            s.refreshInfo()
            self.oldMsg = s.getUnreadMsgCount()
            self.newMsg = 0
            if self.oldMsg == 0:#no unread messages, we need to clear the watch
                self.actually_updated=False
                self.specto.notifier.clear_watch("", self.id)
            else:
                i=0
                while i < self.oldMsg:
                    info = s.getMsgAuthorName(i) + s.getMsgTitle(i) + s.getMsgSummary(i) #create unique info
                    if info not in self.mail_info: #check if it is a new email or just unread
                        self.actually_updated=True
                        self.mail_info.append(info)
                        self.newMsg+=1
                    i+=1
        except:
            self.error = True
            self.specto.logger.log(_("Watch: \"%s\" has error: wrong username/password") % self.name, "error", self.__class__)
            
        self.specto.mark_watch_busy(False, self.id)
        Watch.update(self, lock)
        
    def set_username(self, username):
        """ Set the username for the watch. """
        self.user = username
        
    def set_password(self, password):
        """ Set the password for the watch. """
        self.password = password
