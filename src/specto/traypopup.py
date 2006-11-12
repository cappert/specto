#!/usr/bin/env python
# -*- coding: UTF8 -*-

# Specto , Unobtrusive event notifier
#
#       traypopup.py
#
# Copyright (c) 2005-2007, Jean-François Fortin Tam
# Most of the code in this module is taken from gmail-notify 1.6.1

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

class TrayPopupMenu:
    """
    Create a menu for the Trayicon. 
    """
    
    def __init__(self, specto, text):
        # Create menu items
        self.item_show = gtk.MenuItem( text, True)
        self.item_pref = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
        self.item_help = gtk.ImageMenuItem(gtk.STOCK_HELP)
        self.item_about = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
        self.item_quit = gtk.ImageMenuItem(gtk.STOCK_QUIT)

        # Connect the events
        self.item_show.connect( 'activate', specto.show_notifier)
        self.item_pref.connect( 'activate', specto.show_preferences)
        self.item_help.connect( 'activate', specto.show_help)
        self.item_about.connect( 'activate', specto.show_about)
        self.item_quit.connect( 'activate', specto.quit)
        
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
        
    def show_menu(self, event):
        """ Show the trayicon menu. """
        self.menu.popup( None, None, None, event.button, event.time)
