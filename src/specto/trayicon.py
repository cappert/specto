#!/usr/bin/env python
# -*- coding: UTF8 -*-

# Specto , Unobtrusive event notifier
#
#       trayicon.py
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

import egg.trayicon
import gtk
import os, sys
import specto.traypopup
from specto import i18n
from specto.i18n import _

ICON_PATH = "../data/icons/specto_tray_1.png"
ICON2_PATH = "../data/icons/specto_tray_2.png"


def gettext_noop(s):
    return s

class Tray:
    """
    Display a tray icon in the notification area.    
    """
    
    def __init__(self, specto):
        # Create the tray icon object
        self.specto = specto
        self.tray = egg.trayicon.TrayIcon("SpectoTrayIcon")
        self.eventbox = gtk.EventBox()
        self.tray.add(self.eventbox)
        self.eventbox.connect("button_press_event", self.tray_icon_clicked)
        self.eventbox.connect("destroy", self.specto.recreate_tray)
        
        # Create the tooltip for the tray icon
        self.tooltip = gtk.Tooltips()
        
        # Set the image for the tray icon
        self.imageicon = gtk.Image()
        pixbuf = gtk.gdk.pixbuf_new_from_file( ICON_PATH )
        self.imageicon.set_from_pixbuf(pixbuf)
        self.eventbox.add(self.imageicon)
        
        # Show the tray icon
        self.tray.show_all()
        self.show_tooltip({0:0,1:0,2:0})
                
        while gtk.events_pending():
            gtk.main_iteration(True)

    def set_icon_state_excited(self):
        """ Change the tray icon to updated. """
        pixbuf = gtk.gdk.pixbuf_new_from_file( ICON2_PATH )
        self.imageicon.set_from_pixbuf(pixbuf)
        
    def set_icon_state_normal(self):
        """ Change the tray icon to not updated. """
        pixbuf = gtk.gdk.pixbuf_new_from_file( ICON_PATH )
        self.imageicon.set_from_pixbuf(pixbuf)
                
    def tray_icon_clicked(self,signal,event):
        """
        Create the popupmenu or call show_notifier to hide/show the notifier.
        """
        if event.button == 3:
            if self.specto.notifier.get_state() == True:
                text = _("Hide window")
            else:
                text = _("Show window")
            popup = specto.traypopup.TrayPopupMenu(self, text)
            popup.show_menu(event)
            
        elif event.button == 1:
            self.show_notifier(event)

    def show_tooltip(self, updated_messages):
        """ Create the tooltip message and show the tooltip. """
        global _
        show_return = False
        
        if updated_messages.values() == [0,0,0]:
            message = _("No updated watches.")
        else:
            message = _('Updated watches:\n')
            if updated_messages[0] > 0:
                gettext = _
                _ = gettext_noop
                type = i18n._translation.ungettext(_(" website"), _(" websites"), updated_messages[0])#FIXME: gettext does not work here
                _ = gettext

                message = message + "\t" + str(updated_messages[0]) + str(type)
                show_return = True
            #mail tooltip
            if updated_messages[1] > 0:
                gettext = _        
                _ = gettext_noop
                type = i18n._translation.ungettext(_(" mail"), _(" mails"), updated_messages[1])#FIXME: gettext does not work here
                _ = gettext

                if show_return:
                    message = message + "\n"
                message = message + "\t" + str(updated_messages[1]) + str(type)
                show_return = True
            #file tooltip
            if updated_messages[2] > 0:
                gettext = _
                _ = gettext_noop
                type = i18n._translation.ungettext(_(" file/folders"), _(" files/folders"), updated_messages[2])#FIXME: gettext does not work here
                _ = gettext

                if show_return:
                    message = message + "\n"
                message = message + "\t" + str(updated_messages[2]) + str(type)
        self.tooltip.set_tip(self.tray,message)
            
    def show_preferences(self, widget):
        """ Call the main function to show the preferences window. """
        self.specto.show_preferences() 

    def show_help(self, widget):
        """ Call the main function to show help. """
        self.specto.show_help()
        
    def show_about(self, widget):
        """ Call the main function to show the about window. """
        self.specto.show_about()
        
    def show_notifier(self, widget):
        """ Call the main function to show the notifier window. """
        self.specto.toggle_notifier()
        
    def quit(self, widget):
        """ Call the main function to quit specto. """
        self.specto.quit()
