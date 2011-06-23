# -*- coding: utf-8 -*-

# Specto , Unobtrusive event notifier
#
#       preferences.py
#
# See the AUTHORS file for copyright ownership information

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
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

import os
try:
    import pygtk
    pygtk.require("2.0")
except:
    pass

try:
    import gtk
except:
    pass


class Preferences:
    """
    Display the preferences window.
    """

    def __init__(self, specto, notifier):
        self.specto = specto
        self.notifier = notifier
        uifile = os.path.join(self.specto.PATH, "uis/preferences.ui")
        windowname = "preferences"
        self.builder = gtk.Builder()
        self.builder.set_translation_domain("specto")
        self.builder.add_from_file(uifile)

        #catch some events
        dic = {"on_cancel_clicked": self.delete_event,
              "on_preferences_delete_event": self.delete_event,
              "on_save_clicked": self.save_clicked,
              "on_help_clicked": self.help_clicked,
              "on_chkSoundChanged_toggled": self.chkSoundChanged_toggled,
              "on_chkSoundProblem_toggled": self.chkSoundProblem_toggled,
              "on_button_log_clear_clicked": self.specto.logger.clear_log,
              "on_button_log_open_clicked": self.notifier.show_error_log}

        #attach the events
        self.builder.connect_signals(dic)

        self.preferences = self.builder.get_object("preferences")

        #set the preferences
        self.get_preferences()

    def save_clicked(self, widget):
        """ Save the preferences. """
        self.preferences.hide()
        self.set_preferences()
        self.notifier.show_watch_info()

    def chkSoundChanged_toggled(self, widget):
        """ Make the filechooser sensitive or insensitive. """
        if widget.get_active():
            self.builder.get_object("soundChanged").set_property('sensitive', 1)
        else:
            self.builder.get_object("soundChanged").set_property('sensitive', 0)

    def chkSoundProblem_toggled(self, widget):
        """ Make the filechooser sensitive or insensitive. """
        if widget.get_active():
            self.builder.get_object("soundProblem").set_property('sensitive', 1)
        else:
            self.builder.get_object("soundProblem").set_property('sensitive', 0)

    def set_preferences(self):
        """ Save the preferences in gconf. """
        #save the path for the "changed" sound
        if self.builder.get_object("soundChanged").\
                        get_property('sensitive') == 1:
            self.specto.specto_gconf.set_entry("changed_sound", \
                            self.builder.get_object("soundChanged")\
                                                    .get_filename())
            self.specto.specto_gconf.set_entry("use_changed_sound", True)
        else:
            self.specto.specto_gconf.unset_entry("use_changed_sound")

        #save the path from the problem sound
        if self.builder.get_object("soundProblem").\
                        get_property('sensitive') == 1:
            self.specto.specto_gconf.set_entry("problem_sound", \
                        self.builder.get_object("soundProblem").get_filename())
            self.specto.specto_gconf.set_entry("use_problem_sound", True)
        else:
            self.specto.specto_gconf.unset_entry("use_problem_sound")

        #see if pop toast has to be saved
        if self.builder.get_object("chk_libnotify").get_active():
            self.specto.specto_gconf.set_entry("pop_toast", True)
        else:
            self.specto.specto_gconf.set_entry("pop_toast", False)

        #see if tray has to be saved
        if self.builder.get_object("chk_tray").get_active():
            self.specto.specto_gconf.set_entry("always_show_icon", True)
        else:
            self.specto.specto_gconf.set_entry("always_show_icon", False)
        if not self.notifier.indicator:
            self.notifier.recreate_tray()

        #see if debug mode has to be saved
        if self.builder.get_object("chk_debug").get_active():
            self.specto.specto_gconf.set_entry("debug_mode", True)
            self.specto.DEBUG = True
        else:
            self.specto.specto_gconf.set_entry("debug_mode", False)
            self.specto.DEBUG = False

        #use keyring?
        if self.builder.get_object("chkUseKeyring").get_active():
            self.specto.specto_gconf.set_entry("use_keyring", True)
            self.specto.watch_db.convert_passwords(True)
        else:
            self.specto.specto_gconf.set_entry("use_keyring", False)
            self.specto.watch_db.convert_passwords(False)

    def get_preferences(self):
        """ Get the preferences from gconf. """
        #check toast
        if self.specto.specto_gconf.get_entry("pop_toast") == True:
            self.builder.get_object("chk_libnotify").set_active(True)
        else:
            self.builder.get_object("chk_libnotify").set_active(False)

        #check tray
        if self.specto.specto_gconf.get_entry("always_show_icon") == True:
            self.builder.get_object("chk_tray").set_active(True)
        else:
            self.builder.get_object("chk_tray").set_active(False)

        #check "changed" sound
        if self.specto.specto_gconf.get_entry("use_changed_sound"):
            self.builder.get_object("chkSoundChanged").set_active(True)

        if self.specto.specto_gconf.get_entry("changed_sound"):
            self.builder.get_object("soundChanged").\
                set_filename(self.specto.specto_gconf.\
                                get_entry("changed_sound"))

        #check problem sound
        if self.specto.specto_gconf.get_entry("use_problem_sound"):
            self.builder.get_object("chkSoundProblem").set_active(True)

        if self.specto.specto_gconf.get_entry("problem_sound"):
            self.builder.get_object("soundProblem").\
                set_filename(self.specto.specto_gconf.\
                    get_entry("problem_sound"))

        #check debug
        if self.specto.specto_gconf.get_entry("debug_mode") == True:
            self.builder.get_object("chk_debug").set_active(True)
        else:
            self.builder.get_object("chk_debug").set_active(False)

        if self.specto.specto_gconf.get_entry("use_keyring") == True:
            self.builder.get_object("chkUseKeyring").set_active(True)
        else:
            self.builder.get_object("chkUseKeyring").set_active(False)

    def help_clicked(self, widget):
        """ Show the help webpage. """
        self.specto.show_help()

    def delete_event(self, widget, *args):
        """ Hide the window. """
        self.preferences.hide()
        return True


if __name__ == "__main__":
    #run the gui
    app = Preferences()
    gtk.main()
