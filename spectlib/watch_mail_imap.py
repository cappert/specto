#!/usr/bin/env python
# -*- coding: UTF8 -*-

# Specto , Unobtrusive event notifier
#
#       watch_mail_imap.py
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

import imaplib
import string
from socket import error
from spectlib.i18n import _
import thread
import gtk, time

class Mail_watch(Watch):
    """ 
    Watch class that will check if you recevied a new mail on your imap account. 
    """
    updated = False
    type = 1
    prot = 1
    
    def __init__(self, refresh, host, username, password, ssl, specto, id, name = _("Unknown Mail Watch")):
        Watch.__init__(self, specto)
        self.name = name
        self.refresh = refresh
        self.host = host
        self.user = username
        self.password = password
        self.id = id
        self.error = False
        self.ssl = ssl
        
    def dict_values(self):
        return { 'name': self.name, 'refresh': self.refresh, 'username': self.user, 'password':self.password, 'host':self.host, 'ssl':self.ssl, 'type':1, 'prot':1 }
        
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
        """ Check for new mails on your imap account. """
        self.error = False
        self.specto.update_watch(True, self.id)
        self.specto.logger.log(_("Updating watch: \"%s\"") % self.name, "info", self.__class__)
           
        try:
            if str(self.ssl) == 'True':
                server = imaplib.IMAP4_SSL(self.host)
            else:
                server = imaplib.IMAP4(self.host)
        except error, e:
            self.error = True
            self.specto.logger.log(_("Watch: \"%s\" has error: %s") % (self.name, str(e)), "error", self.__class__)
        else:
            try:
                server.login(self.user, self.password)
                folders = server.list()[1] 
                folders.append('(HasChildren) "." "INBOX"')
                for folder in folders: 
                    folderName = folder.split()[2] 
        
                    if folderName == '"."': 
                        continue 
                    totalMsgs = server.select(folderName)[1][0]
         
                    if totalMsgs.startswith(_("Mailbox does not exist")): 
                        continue 
                    r, data = server.search(None, "(NEW)")
                    newMsgs = data[0] #server.recent()[1][0] 
                    
                    if newMsgs != "":
                        self.updated = True            
                server.logout()
            
            except imaplib.IMAP4.error, e:
                self.error = True
                self.specto.logger.log(_("Watch: \"%s\" has error: %s") % (self.name, str(e)), "error", self.__class__)
            
        self.specto.update_watch(False, self.id)
        lock.release()
        Watch.update(self)
                    
    def set_username(self, username):
        """ Set the username. """
        self.user = username
        
    def set_password(self, password):
        """ Set the password. """
        self.password = password
        
    def set_host(self, host):
        """ Set the host. """
        self.host = host
        
    def set_ssl(self, ssl):
        """ Use ssl support. """
        self.ssl = ssl
