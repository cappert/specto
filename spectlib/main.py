# -*- coding: UTF8 -*-

# Specto , Unobtrusive event notifier
#
#       main.py
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

# Definition of the watch_db
# watch_db[0] = instance of the first watch

global GTK
global DEBUG #the DEBUG constant which controls how much info is output

import os, sys, gobject

import spectlib.util as util
from spectlib.watch import Watch_collection, Watch_io
from spectlib.console import Console
from spectlib.logger import Logger
from spectlib.tools.specto_gconf import Specto_gconf
from spectlib.i18n import _
from spectlib.tools import networkmanager as conmgr

#create a gconf object
specto_gconf = Specto_gconf("/apps/specto")

if specto_gconf.get_entry("debug_mode")==True:
    DEBUG = True
elif specto_gconf.get_entry("debug_mode")==False:
    DEBUG = False
else:
    DEBUG = False

try:
    import pygtk
    pygtk.require("2.0")
    import gtk
    import gtk.glade
except:
    print _("no GTK, activating console mode")
    GTK = False
else:
    GTK = True
    from spectlib.notifier import Notifier
        
class Specto:
    """ The main Specto class. """

    def __init__(self):
        self.DEBUG = DEBUG
        self.util = util
        
        self.PATH = self.util.get_path()
        self.SRC_PATH = self.util.get_path("src")
        self.SPECTO_DIR = self.util.get_path("specto")
        self.CACHE_DIR = self.util.get_path("tmp")
        self.FILE = self.util.get_file()

        import gettext #this is for the glade files
        self.glade_gettext = gettext.textdomain("specto")
        self.logger = Logger(self)
        self.check_instance() #see if specto is already running
        self.specto_gconf = specto_gconf
        self.check_default_settings()#if this is the first run of specto, set the default values for gconf. Whenever you add some gconf preference for specto, this function will also need to be updated.
        self.GTK = GTK
                
        self.connection_manager = conmgr.get_net_listener()
        self.use_keyring = self.specto_gconf.get_entry("use_keyring")

        #create the watch collection and add the watches
        self.watch_db = Watch_collection(self)
        self.watch_io = Watch_io(self, self.FILE)
        values = self.watch_io.read_all_watches()
        try:
            self.watch_db.create(values)
        except AttributeError, error_fields:
            self.logger.log("Specto could not create a corrupted watch.", "critical", "Specto")

        if sys.argv[1:]:
            if "--console" in sys.argv[1:][0]:
                self.logger.log("Console mode enabled.", "debug", "Specto")
                self.GTK = False
                self.CONSOLE = True
                try:
                    args = sys.argv[1:][1]
                except:
                    args = ""
                self.console = Console(self, args)
                self.console.start_watches()
                                
        elif self.GTK:
            self.GTK = True
            self.CONSOLE = False
            self.icon_theme = gtk.icon_theme_get_default()
            self.notifier = Notifier(self)
            
        #listen for gconf keys
        self.specto_gconf.notify_entry("debug_mode", self.key_changed, "debug")
        
        if self.GTK:
            if self.specto_gconf.get_entry("always_show_icon") == False:
                #if the user has not requested the tray icon to be shown at all times, it's impossible that the notifier is hidden on startup, so we must show it.
                self.notifier_hide = False
            elif self.specto_gconf.get_entry("show_notifier")==True:
                self.notifier_hide = False
                self.toggle_notifier()
            elif self.specto_gconf.get_entry("show_notifier")==False:
                self.notifier_hide = True
            else:#just in case the entry was never created in gconf
                self.notifier_keep_hidden = False
            
            for watch in self.watch_db:
                self.notifier.add_notifier_entry(watch.id)
                
            self.notifier.refresh_all_watches()
            
        if self.GTK:
            gtk.main()
        else:
            try:
                self.go = gobject.MainLoop()
                self.go.run()
            except (KeyboardInterrupt, SystemExit):
                sys.exit(0)

    def key_changed(self, *args):
        """ Listen for gconf keys. """
        label = args[3]
        
        if label == "debug":
            self.DEBUG = self.specto_gconf.get_entry("debug_mode")

    def check_default_settings(self):
        """ This is used to set the default settings properly the first time Specto is run, without using gconf schemas """
        #check if the ekiga sounds exists
        if os.path.exists("/usr/share/sounds/ekiga/voicemail.wav"):
            changed_sound = "/usr/share/sounds/ekiga/voicemail.wav"
        else:
            changed_sound = ""
            
        self.default_settings=(
            ["always_show_icon", False], #having it True would be against the HIG!
            ["debug_mode", False],
            ["follow_website_redirects", True],
            ["pop_toast_duration", 5],
            ["pop_toast", True],
            ["show_deactivated_watches", True],
            ["show_in_windowlist", True],
            ["show_notifier", True],
            ["show_toolbar", True],
            ["sort_function", "name"],
            ["sort_order", "asc"],
            ["changed_sound", changed_sound],
            ["use_changed_sound", False],
            ["window_notifier_height", 500],
            ["window_notifier_width", 500],
            ["use_keyring", True]
            )
        for default_setting in self.default_settings:
            if self.specto_gconf.get_entry(default_setting[0]) == None: #the key has no user-defined value or does not exist
                self.specto_gconf.set_entry(default_setting[0], default_setting[1])

    def set_passwords(self, use_keyring):
        self.watch_io.keyring = use_keyring
        for watch in self.watch_db:
            try:
                self.watch_io.write_option(watch.name, "password", watch.password)
            except:
                pass
                
    def check_instance(self):
        """ Check if specto is already running. """
        pidfile = self.SPECTO_DIR + "/" + "specto.pid"
        if not os.path.exists(pidfile):
            f = open(pidfile, "w")
            f.close()
        os.chmod(pidfile, 0600)
        
        #see if specto is already running
        f=open(pidfile, "r")
        pid = f.readline()
        f.close()
        if pid:    
            p=os.system("ps --no-heading --pid " + pid)
            p_name=os.popen("ps -f --pid " + pid).read()
            if p == 0 and "specto" in p_name:
                self.logger.log(_("Specto is already running!"), "critical", self.__class__)
                sys.exit(0)
            
        #write the pid file
        f=open(pidfile, "w")
        f.write(str(os.getpid()))
        f.close()        
                
    def mark_watch_status(self, status, id):
        """ get the watch status (checking, changed, idle) """
        if self.GTK:
            self.notifier.mark_watch_status(status, id)
        elif self.CONSOLE:
            self.console.mark_watch_status(status, id)

    def toggle_notifier(self, *args):
        """
        Toggle the state of the notifier, hidden or shown.
        It will save the size, position, and the last state when you closed Specto.
        """
        #Creating the notifier window, but keeping it hidden
        if self.notifier.get_state()==True and not self.notifier_hide:
            self.specto_gconf.set_entry("show_notifier", True)
            self.notifier.restore_size_and_position()#to make sure that the x and y positions don't jump around
            self.notifier.notifier.show()
            self.notifier_hide = True
        elif self.notifier.get_state()==True and self.notifier_hide:
            self.notifier.save_size_and_position()
            self.specto_gconf.set_entry("show_notifier", False)
            self.notifier.notifier.hide()
            self.notifier_hide = False
        else:
            self.specto_gconf.set_entry("show_notifier", True)
            self.notifier.restore_size_and_position()#to make sure that the x and y positions don't jump around
            self.notifier.notifier.show()
            self.notifier_hide = True
       
    def quit(self, *args):
        """ Save the save and position from the notifier and quit Specto. """
        if self.notifier.get_state()==True and self.notifier_hide:
            self.notifier.save_size_and_position()#when quitting specto abruptly, remember the notifier window properties
        try:
            gtk.main_quit()
        except:
            #create a close dialog
            dialog = gtk.Dialog(_("Cannot quit yet"), None, gtk.DIALOG_MODAL | gtk.DIALOG_NO_SEPARATOR | gtk.DIALOG_DESTROY_WITH_PARENT, None)
            #HIG tricks
            dialog.set_has_separator(False)
            
            dialog.add_button(_("Murder!"), 3)
            dialog.add_button(gtk.STOCK_CANCEL, -1)

            dialog.label_hbox = gtk.HBox(spacing=6)
            
            
            icon = gtk.Image()
            icon.set_from_pixbuf(self.icon_theme.load_icon("dialog-warning", 64, 0))
            dialog.label_hbox.pack_start(icon, True, True, 6)
            icon.show()

            label = gtk.Label(_('<b><big>Specto is currently busy and cannot quit yet.</big></b>\n\nThis may be because it is checking for watch changes.\nHowever, you can try forcing it to quit by clicking the murder button.'))
            label.set_use_markup(True)
            dialog.label_hbox.pack_start(label, True, True, 6)#here, pack means "cram the label right at the start of the vbox before the buttons"
            label.show()
            
            dialog.vbox.pack_start(dialog.label_hbox, True, True, 12)
            dialog.label_hbox.show()
            
            icon = gtk.gdk.pixbuf_new_from_file(self.PATH + 'icons/specto_window_icon.svg' )
            dialog.set_icon(icon)
            answer = dialog.run()
            if answer == 3:
                try:#go figure, it never works!
                    self.notifier.stop_refresh = True
                    sys.exit(0)
                except:
                    #kill the specto process with killall
                    os.system('killall specto')
            else:
                dialog.destroy()
