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
from spectlib.i18n import _
from spectlib.gmailatom import GmailAtom

type = "Mail_watch_gmail"

class Mail_watch_gmail(Watch):
    """
    this watch will check if you have a new mail on your gmail account
    """
    use_network = True
    icon = "emblem-mail"

    def __init__(self,specto, id, values):
        Watch.__init__(self, specto, id, values['name'], int(values['refresh']), values['type'])
        self.oldMsg = 0
        self.newMsg = 0
        self.mail_info = []
        
        if "@" not in values['username']:
            self.user = values['username'] + "@gmail.com"
        else:
            self.user = values['username']
        self.password = values['password']
        
    def dict_values(self):
        return { 'name': self.name, 'refresh': self.refresh, 'username': self.user, 'password':self.password, 'type':1, 'prot':2 }
        
    def update(self):
        """ Check for new mails on your gmail account. """
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
                    info = str(s.getMsgAuthorName(i) + "|" + s.getMsgTitle(i) + "|" + s.getMsgSummary(i)) #create unique info
                    if info not in self.mail_info: #check if it is a new email or just unread
                        self.actually_updated=True
                        self.mail_info.append(info)
                        self.newMsg+=1
                    i+=1
        except:
            self.error = True
            self.specto.logger.log(_("Watch: \"%s\" has error: wrong username/password") % self.name, "error", self.__class__)
        print "update gedaan"
        Watch.timer_update(self)
        
    def set_username(self, username):
        """ Set the username for the watch. """
        self.user = username
        
    def set_password(self, password):
        """ Set the password for the watch. """
        self.password = password
        
    def get_balloon_text(self):
        """ create the text for the balloon """
        if self.newMsg == 1:
            text = ("<b>%s</b> has received a new message from <b>%s</b>\n\n <b>totalling %d</b> unread mails.") % (self.name, self.mail_info[self.oldMsg-1].split("|")[0], self.newMsg)
        else:
            i = self.newMsg - self.oldMsg
            y = 0 #show max 4 mails
            author_info = ""
            while i < len(self.mail_info) and y < 5:
                author_info += self.mail_info[i].split("|")[0] + ", "
                i+=1
                y+=1
                if y == 5:
                    author_info += "and others..."
            
            author_info = author_info.rstrip(", ")    
            text = ("<b>%s</b> has received a new message from <b>%s</b>\n\n <b>totalling %d</b> unread mails.") % (self.name, author_info, self.newMsg)    
        return text
    
    def get_extra_information(self):
        i = self.newMsg - self.oldMsg
        y = 0
        author_info = ""
        while i < len(self.mail_info) and y < 5:
            author_info += "<i>" + self.mail_info[i].split("|")[1] + "</i> From <b>" + self.mail_info[i].split("|")[0] + "</b>\n"
            i += 1
            y += 1
            if y == 5:
                author_info += "and others..."
        text = "<b>New messages:</b>\n" + author_info
        return text
 
def get_gui_info(self):
    return {"Name": self.name}

