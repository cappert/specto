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
from spectlib.i18n import _

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
        self.wTree=gtk.glade.XML(gladefile,windowname, self.specto.glade_gettext)
        
        #catch some events
        dic= { "on_cancel_clicked": self.delete_event,
        "on_preferences_delete_event": self.delete_event,
        "on_save_clicked": self.save_clicked,
        "on_help_clicked": self.help_clicked,
        "on_chkSoundUpdate_toggled": self.chkSoundUpdate_toggled,
        "on_chkSoundProblem_toggled": self.chkSoundProblem_toggled,
        "on_chk_libnotify_toggled": self.chkLibnotify_toggled,
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

    def chkLibnotify_toggled(self, widget):
        """ Make the slider below the libnotify checkbox insensitive or not """
        if widget.get_active():
            self.wTree.get_widget("hbox_libnotify_duration").set_property('sensitive', 1)
        else:
            self.wTree.get_widget("hbox_libnotify_duration").set_property('sensitive', 0)

    def set_preferences(self):
        """ Save the preferences in gconf. """
        self.specto.logger.log(_("Preferences saved."), "info", self.__class__)

        #save the path from the update sound
        if self.wTree.get_widget("soundUpdate").get_property('sensitive') == 1:
            self.specto.specto_gconf.set_entry("update_sound", self.wTree.get_widget("soundUpdate").get_filename())
            self.specto.specto_gconf.set_entry("use_update_sound", True)
        else:
            self.specto.specto_gconf.unset_entry("use_update_sound")

        #save the path from the problem sound
        if self.wTree.get_widget("soundProblem").get_property('sensitive') == 1:
            self.specto.specto_gconf.set_entry("problem_sound", self.wTree.get_widget("soundProblem").get_filename())
            self.specto.specto_gconf.set_entry("use_problem_sound", True)
        else:
            self.specto.specto_gconf.unset_entry("use_problem_sound")

        #see if pop toast has to be saved
        if self.wTree.get_widget("chk_libnotify").get_active():
            self.specto.specto_gconf.set_entry("pop_toast", True)
            self.specto.specto_gconf.set_entry("pop_toast_duration", int(self.wTree.get_widget("hscale_libnotify_duration").get_value() ))#save the pop toast duration
        else:
            self.specto.specto_gconf.set_entry("pop_toast", False)

        #see if windowlist has to be saved
        if self.wTree.get_widget("chk_windowlist").get_active():
            self.specto.specto_gconf.set_entry("show_in_windowlist", True)
            self.specto.notifier.notifier.set_skip_taskbar_hint(True)
        else:
            self.specto.specto_gconf.set_entry("show_in_windowlist", True)
            self.specto.notifier.notifier.set_skip_taskbar_hint(False)#note, this is set_SKIP! this explains why it's False to skip.

        #see if tray has to be saved
        if self.wTree.get_widget("chk_tray").get_active():
            self.specto.specto_gconf.set_entry("always_show_icon", True)
        else:
            self.specto.specto_gconf.set_entry("always_show_icon", False)
        self.specto.recreate_tray()

        #see if debug mode has to be saved
        if self.wTree.get_widget("chk_debug").get_active():
            self.specto.specto_gconf.set_entry("debug_mode", True)
        else:
            self.specto.specto_gconf.set_entry("debug_mode", False)







    def get_preferences(self):
        """ Get the preferences from gconf. """
        #check toast
        if self.specto.specto_gconf.get_entry("pop_toast") == True:
            self.wTree.get_widget("chk_libnotify").set_active(True)
            self.wTree.get_widget("hbox_libnotify_duration").set_property('sensitive', 1)
        else:
            self.wTree.get_widget("chk_libnotify").set_active(False)
            self.wTree.get_widget("hbox_libnotify_duration").set_property('sensitive', 0)
        #set the toast duration properly
        if not self.specto.specto_gconf.get_entry("pop_toast_duration"):
            pass#nothing was set, leave the value at 5
        else:
            self.wTree.get_widget("hscale_libnotify_duration").set_value(self.specto.specto_gconf.get_entry("pop_toast_duration"))

        #check windowlist
        if self.specto.specto_gconf.get_entry("show_in_windowlist") == True:
            self.wTree.get_widget("chk_windowlist").set_active(True)
        else:
            self.wTree.get_widget("chk_windowlist").set_active(False)

        #check tray
        if self.specto.specto_gconf.get_entry("always_show_icon") == True:
            self.wTree.get_widget("chk_tray").set_active(True)
        else:
            self.wTree.get_widget("chk_tray").set_active(False)
        
        #check update sound
        if self.specto.specto_gconf.get_entry("use_update_sound"):
            self.wTree.get_widget("chkSoundUpdate").set_active(True)
            
        if self.specto.specto_gconf.get_entry("update_sound"):
            self.wTree.get_widget("soundUpdate").set_filename(self.specto.specto_gconf.get_entry("update_sound"))

        #check problem sound
        if self.specto.specto_gconf.get_entry("use_problem_sound"):
            self.wTree.get_widget("chkSoundProblem").set_active(True)
            
        if self.specto.specto_gconf.get_entry("problem_sound"):
            self.wTree.get_widget("soundProblem").set_filename(self.specto.specto_gconf.get_entry("problem_sound"))
            
        #check debug
        if self.specto.specto_gconf.get_entry("debug_mode") == True:
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
