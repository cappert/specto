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

import gtk
import os, sys
from spectlib import i18n
from spectlib.i18n import _

def gettext_noop(s):
    return s

class Tray:
    """
    Display a tray icon in the notification area.    
    """
    def __init__(self, specto):
        self.specto = specto
        self.ICON_PATH = self.specto.PATH + "icons/specto_tray_1.png"
        self.ICON2_PATH = self.specto.PATH + "icons/specto_tray_2.png"
        # Create the tray icon object
        self.tray=None
        if not self.tray: self.tray = gtk.StatusIcon()
        self.tray.set_from_file(self.ICON_PATH)
        self.tray.connect("activate", self.show_notifier)
        self.tray.connect("popup-menu", self.show_popup)
        if self.specto.conf_pref.get_entry("/always_show_icon", "boolean") == True:
            self.tray.set_visible(True)
        else:
            self.tray.set_visible(False)      

        while gtk.events_pending():
            gtk.main_iteration(True)

    def set_icon_state_excited(self):
        """ Change the tray icon to updated. """
        if self.specto.conf_pref.get_entry("/always_show_icon", "boolean") == False:
            self.tray.set_from_file( self.ICON2_PATH )
            self.tray.set_visible(True)#we need to show the tray again
        else:
            self.tray.set_from_file( self.ICON2_PATH )
        
    def set_icon_state_normal(self):
        """ Change the tray icon to not updated. If the user requested to always show the tray, it will change its icon but not disappear. Otherwise, it will be removed."""
        if self.specto.conf_pref.get_entry("/always_show_icon", "boolean") == False:
            self.tray.set_visible(False)
        else:
            self.tray.set_from_file( self.ICON_PATH )

    def show_tooltip(self, updated_messages):
        """ Create the tooltip message and show the tooltip. """
        global _
        show_return = False
        
        if updated_messages.values() == [0,0,0]:
            message = _("No updated watches.")
        else:
            message = _('Updated watches:\n')
            if updated_messages[0] > 0:
                type = i18n._translation.ungettext(_("website"), _("websites"), updated_messages[0])

                message = message + "\t" + str(updated_messages[0]) + " " + type
                show_return = True
            #mail tooltip
            if updated_messages[1] > 0:
                type = i18n._translation.ungettext(_("mail account"), _("mail accounts"), updated_messages[1])

                if show_return:
                    message = message + "\n"
                message = message + "\t" + str(updated_messages[1]) + " " + type
                show_return = True
            #file tooltip
            if updated_messages[2] > 0:
                type = i18n._translation.ungettext(_("file/folder"), _("files/folders"), updated_messages[2])

                if show_return:
                    message = message + "\n"
                message = message + "\t" + str(updated_messages[2]) + " " + type
        self.tray.set_tooltip(message)
            
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
        if self.specto.conf_pref.get_entry("/always_show_icon", "boolean") == True:
            self.specto.toggle_notifier()
        else:
            self.specto.notifier.notifier.present()

    def show_popup(self, status_icon, button, activate_time):
        """
        Create the popupmenu
        """
        ## From the PyGTK 2.10 documentation
        # status_icon :	the object which received the signal
        # button :	the button that was pressed, or 0 if the signal is not emitted in response to a button press event
        # activate_time :	the timestamp of the event that triggered the signal emission
        if self.specto.conf_pref.get_entry("/always_show_icon", "boolean") == True and self.specto.notifier.get_state() == True:
            text = _("Hide window")
        else:
            text = _("Show window")

        # Create menu items
        self.item_show = gtk.MenuItem( text, True)
        self.item_pref = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
        self.item_help = gtk.ImageMenuItem(gtk.STOCK_HELP)
        self.item_about = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
        self.item_quit = gtk.ImageMenuItem(gtk.STOCK_QUIT)

        # Connect the events
        self.item_show.connect( 'activate', self.show_notifier)
        self.item_pref.connect( 'activate', self.show_preferences)
        self.item_help.connect( 'activate', self.show_help)
        self.item_about.connect( 'activate', self.show_about)
        self.item_quit.connect( 'activate', self.quit)
        
        # Create the menu
        self.menu = gtk.Menu()
        
        # Append menu items to the menu
        self.menu.append( self.item_show)
        self.menu.append( gtk.SeparatorMenuItem())
        self.menu.append( self.item_pref)
        self.menu.append( self.item_help)
        self.menu.append( self.item_about)
        self.menu.append( gtk.SeparatorMenuItem())
        self.menu.append( self.item_quit)
        self.menu.show_all()
        self.menu.popup(None, None, gtk.status_icon_position_menu, button, activate_time, self.tray)#the last argument is to tell gtk.status_icon_position_menu where to grab the coordinates to position the popup menu correctly

    #grab the x and y position of the tray icon and make the balloon emerge from it
    def get_x(self):
        x = self.tray.get_geometry()[1][0]
        if self.tray.get_visible()==True:
            x += int(self.tray.get_size() / 2) #add half the icon's width
        else:
            x -= int(self.tray.get_size() / 2) #remove half the icon's width
            #FIXME: I don't know why that one does not work
        return x
    def get_y(self):
        y = self.tray.get_geometry()[1][1]
        if self.tray.get_visible()==True:
            y += int(self.tray.get_size() / 2) #add half the icon's height
        else:
            y -= int(self.tray.get_size() / 2) #remove half the icon's height
            #FIXME: I don't know why that one does not work
        return y

    def destroy(self):
        self.tray.set_visible(False)
        
    def quit(self, widget):
        """ Call the main function to quit specto. """
        self.specto.quit()
