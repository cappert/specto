#!/usr/bin/env python
# -*- coding: UTF8 -*-

# Specto , Unobtrusive event notifier
#
#       preferences.py
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

import sys, os
from specto.i18n import _

try:
    import pygtk
    pygtk.require("2.0")
except:
    pass

try:
    import gtk
    import gtk.glade
except:
    pass

class Preferences:
    """
    Display the preferences window.
    """
    
    def __init__(self, specto):
        self.specto = specto
        gladefile= self.specto.PATH + 'glade/preferences.glade'
        windowname= "preferences"
        self.wTree=gtk.glade.XML(gladefile,windowname)
        
        #catch some events
        dic= { "on_cancel_clicked": self.delete_event,
        "on_preferences_delete_event": self.delete_event,
        "on_save_clicked": self.save_clicked,
        "on_help_clicked": self.help_clicked,
        "on_chkSoundUpdate_toggled": self.chkSoundUpdate_toggled,
        "on_chkSoundProblem_toggled": self.chkSoundProblem_toggled,
        "on_button_log_clear_clicked": self.specto.logger.clear_log,
        "on_button_log_open_clicked": self.specto.show_error_log
        }
        
        #attach the events
        self.wTree.signal_autoconnect(dic)
        
        self.preferences=self.wTree.get_widget("preferences")

        #set the preferences
        self.get_preferences()

    def save_clicked(self, widget):
        """ Save the preferences. """
        self.preferences.hide()
        self.set_preferences()

    def chkSoundUpdate_toggled(self, widget):
        """ Make the filechooser sensitive or insensitive. """
        client = self.specto.GConfClient("/apps/specto/preferences")
        if widget.get_active():
            self.wTree.get_widget("soundUpdate").set_property('sensitive', 1)
        else:
            self.wTree.get_widget("soundUpdate").set_property('sensitive', 0)

    def chkSoundProblem_toggled(self, widget):
        """ Make the filechooser sensitive or insensitive. """
        if widget.get_active():
            self.wTree.get_widget("soundProblem").set_property('sensitive', 1)
        else:
            self.wTree.get_widget("soundProblem").set_property('sensitive', 0)

    def set_preferences(self):
        """ Save the preferences in gconf. """
        self.specto.logger.log(_("Preferences saved."), "info", self.__class__)
        #create a gconf object
        client = self.specto.GConfClient("/apps/specto/preferences")
        
        #save the path from the update sound
        if self.wTree.get_widget("soundUpdate").get_property('sensitive') == 1:
            client.set_entry("/update_sound", self.wTree.get_widget("soundUpdate").get_filename(), "string")
            client.set_entry("/use_update_sound", 1, "boolean")
        else:
            client.unset_entry("/use_update_sound")

        #save the path from the problem sound
        if self.wTree.get_widget("soundProblem").get_property('sensitive') == 1:
            client.set_entry("/problem_sound", self.wTree.get_widget("soundProblem").get_filename(), "string")
            client.set_entry("/use_problem_sound", 1, "boolean")
        else:
            client.unset_entry("/use_problem_sound")

        #see if pop toast has to be saved
        if self.wTree.get_widget("chk_libnotify").get_active():
            client.set_entry("/pop_toast",1, "boolean")
        else:
            client.set_entry("/pop_toast",0, "boolean")

        #see if windowlist has to be saved
        if self.wTree.get_widget("chk_windowlist").get_active():
            client.set_entry("/windowlist", 1, "boolean")
        else:
            client.set_entry("/windowlist", 0, "boolean")

        #see if debug mode has to be saved
        if self.wTree.get_widget("chk_debug").get_active():
            client.set_entry("/debug_mode",1, "boolean")
        else:
            client.set_entry("/debug_mode",0, "boolean")

    def get_preferences(self):
        """ Get the preferences from gconf. """
        #create a gconf object
        client = self.specto.GConfClient("/apps/specto/preferences")

        #check toast
        if client.get_entry("/pop_toast", "boolean") == True:
            self.wTree.get_widget("chk_libnotify").set_active(True)
        else:
            self.wTree.get_widget("chk_libnotify").set_active(False)

        #check windowlist
        if client.get_entry("/windowlist", "boolean") == True:
            self.wTree.get_widget("chk_windowlist").set_active(True)
        else:
            self.wTree.get_widget("chk_windowlist").set_active(False)

        #check update sound
        if client.get_entry("/use_update_sound", "boolean"):
            self.wTree.get_widget("chkSoundUpdate").set_active(True)
            
        if client.get_entry("/update_sound", "string"):
            self.wTree.get_widget("soundUpdate").set_filename(client.get_entry("/update_sound", "string"))

        #check problem sound
        if client.get_entry("/use_problem_sound", "boolean"):
            self.wTree.get_widget("chkSoundProblem").set_active(True)
            
        if client.get_entry("/problem_sound", "string"):
            self.wTree.get_widget("soundProblem").set_filename(client.get_entry("/problem_sound", "string"))
            
        #check debug
        if client.get_entry("/debug_mode", "boolean") == True:
            self.wTree.get_widget("chk_debug").set_active(True)
        else:
            self.wTree.get_widget("chk_debug").set_active(False)
    
    def help_clicked(self, widget):
        """ Show the help webpage. """
        self.specto.show_help()
        
    def delete_event(self, widget, *args):
        """ Hide the window. """        
        self.preferences.hide()
        return True
        
if __name__ == "__main__":
    #run the gui
    app=preferences()
    gtk.main()
