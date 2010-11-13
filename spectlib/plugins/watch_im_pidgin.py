# -*- coding: utf-8 -*-

# Specto , Unobtrusive event notifier
#
#       watch_im_pidgin.py
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
import re

type = "Watch_im_pidgin"
type_desc = _("Pidgin")
icon = 'pidgin'
category = _("Social networks")
dbus_watch = True


def get_add_gui_info():
    return [("receivedimmsg_", spectlib.gtkconfig.CheckButton(_("Notify if you receive a IM message"), True)),
            ("receivedchatmsg_", spectlib.gtkconfig.CheckButton(_("Notify if you receive a IM message"), True)),
            ("buddystatuschanged_", spectlib.gtkconfig.CheckButton(_("Notify if a user changes status"))),
            ("buddysignedon_", spectlib.gtkconfig.CheckButton(_("Notify if a user signs on"))),
            ("buddysignedoff_", spectlib.gtkconfig.CheckButton(_("Notify if a user signs off")))
            ]


class Watch_im_pidgin(Watch):
    """
    Watch class that will check pidgin dbus signals.
    """

    def __init__(self, specto, id, values):

        watch_values = [("receivedimmsg_", spectlib.config.Boolean(False)),
                        ("receivedchatmsg_", spectlib.config.Boolean(False)),
                        ("buddystatuschanged_", spectlib.config.Boolean(False)),
                        ("buddysignedon_", spectlib.config.Boolean(False)),
                        ("buddysignedoff_", spectlib.config.Boolean(False))
                        ]

        self.icon = icon
        self.standard_open_command = ''
        self.type_desc = type_desc

        #Init the superclass and set some specto values
        Watch.__init__(self, specto, id, values, watch_values)
        
        self.dbus = True
        self.message = ""
        self.extra_info = ""
        # Use the dbus interface we saw in dbus-notify
        self.dbus_interface = "im.pidgin.purple.PurpleInterface"
        self.dbus_path = "/im/pidgin/purple/PurpleObject"
        self.dbus_name = "im.pidgin.purple.PurpleService"

        self.signals = {
            "ReceivedImMsg": self.ReceivedImMsg,
            "ReceivedChatMsg": self.ReceivedChatMsg,
            "BuddyStatusChanged": self.BuddyStatusChanged,
            "BuddySignedOn": self.BuddySignedOn,
            "BuddySignedOff": self.BuddySignedOff,            
             }
        
        
    def BuddyStatusChanged(self, buddy, old_status, status):
        if not self.buddystatuschanged_:
            return
        
        if buddy != 0:
            pidgin_interface = self.get_pidgin_interface()

            osts = pidgin_interface.PurpleStatusGetName(old_status)
            nsts = pidgin_interface.PurpleStatusGetName(status)

            if osts != nsts:
                name = pidgin_interface.PurpleBuddyGetAlias(buddy)
                self.message = name + ' changed status from ' + osts + ' to ' + nsts
                self.extra_info = self.clean(self.message) + "\n" + self.extra_info
                self.watch_changed()

        
    def BuddySignedOn(self, buddy):
        if not self.buddysignedon_:
            return
        
        if buddy != 0:
            pidgin_interface = self.get_pidgin_interface()

            name = pidgin_interface.PurpleBuddyGetAlias(buddy)
            self.message = name + ' signed on'
            self.extra_info = self.clean(self.message) + "\n" + self.extra_info
            self.watch_changed()

        
    def BuddySignedOff(self, buddy):
        if not self.buddysignedoff_:
            return
        if buddy != 0:
            pidgin_interface = self.get_pidgin_interface()
            
            name = pidgin_interface.PurpleBuddyGetAlias(buddy)
            self.message = name + ' signed off'
            self.extra_info = self.clean(self.message) + "\n" + self.extra_info
            self.watch_changed()
        

    def ReceivedImMsg(self, account, name, message, conversation, flags):
        if not self.receivedimmsg_:
            return
        pidgin_interface = self.get_pidgin_interface()
    
        #TODO figure out if the pidgin window is in focus (not just the conversation)
        #has_focus = pidgin_interface.PurpleConversationHasFocus(conversation)
        has_focus = 1

        if has_focus != 0:
            buddy = pidgin_interface.PurpleFindBuddy(account, name)

            if buddy != 0:
                name = pidgin_interface.PurpleBuddyGetAlias(buddy)
                self.message = name + ": " + message
                self.extra_info = self.clean(self.message) + "\n" + self.extra_info
                self.watch_changed()

    def ReceivedChatMsg(self, account, name, message, conversation, flags):
        if not self.receivedchatmsg_:
            return
        pidgin_interface = self.get_pidgin_interface()

        #TODO figure out if the pidgin window is in focus (not just the conversation)
        #has_focus = pidgin_interface.PurpleConversationHasFocus(conversation)
        has_focus = 1

        if has_focus != 0:
            chatroom_name = pidgin_interface.PurpleConversationGetTitle(conversation)
            chat_data = pidgin_interface.PurpleConversationGetChatData(conversation)

            chat_nick = pidgin_interface.PurpleConvChatGetNick(chat_data)

            if name != chat_nick:
                self.message = chatroom_name + " (" + name + "): " + message
                self.extra_info = self.clean(self.message) + "\n" + self.extra_info 
                self.watch_changed()
                
    def get_pidgin_interface(self):
        pidgin_object = self.session_bus.get_object(self.dbus_name, self.dbus_path)
        return dbus.Interface(pidgin_object, self.dbus_interface)
    
    def get_balloon_text(self):
        """ create the text for the balloon """
        return self.clean(self.message)
    
    def clean(self, s):
        s = re.compile('<[^>]+>').sub(' ',s)
        s = s.replace("&lt;", "<")
        s = s.replace("&gt;", ">")
        s = s.replace("&apos;", "'")
        s = s.replace("&quot;", '"')
        # this has to be last:
        s = s.replace("&amp;", "&")
        return s

    def get_extra_information(self):
        return self.extra_info

    def get_gui_info(self):
        return [(_('Name'), self.name),
                (_('Last changed'), self.last_changed)]
