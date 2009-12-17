# -*- coding: UTF8 -*-

# Specto , Unobtrusive event notifier
#
#       main.py
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

# Definition of the watch_db
# watch_db[0] = instance of the first watch

global GTK
global DEBUG #the DEBUG constant which controls how much info is output

import os
import sys
import signal
import gobject
import gettext

import spectlib.util as util
from spectlib.watch import Watch_collection
from spectlib.watch import Watch_io
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

        self.glade_gettext = gettext.textdomain("specto")
        self.logger = Logger(self)

        self.VERSION = self.get_version_number()  # The Specto version number

        self.GTK = GTK
        if not self.check_instance(): #see if specto is already running
            self.specto_gconf = specto_gconf
            self.check_default_settings()

            self.connection_manager = conmgr.get_net_listener()
            self.use_keyring = self.specto_gconf.get_entry("use_keyring")

            #create the watch collection and add the watches
            self.watch_db = Watch_collection(self)
            self.watch_io = Watch_io(self, self.FILE)

            if (sys.argv[1:] and "--console" in sys.argv[1:][0]) or not self.GTK:
                self.logger.log(_("Console mode enabled."), "debug", "specto")
                self.GTK = False
                self.CONSOLE = True
                try:
                    args = sys.argv[1:][1]
                except:
                    args = ""
                self.console = Console(self, args)

            elif self.GTK:
                self.GTK = True
                self.CONSOLE = False
                self.icon_theme = gtk.icon_theme_get_default()
                self.notifier = Notifier(self)

                if self.specto_gconf.get_entry("always_show_icon") == False:
                    self.notifier_hide = False
                elif self.specto_gconf.get_entry("show_notifier")==True:
                    self.notifier_hide = False
                    self.toggle_notifier()
                elif self.specto_gconf.get_entry("show_notifier")==False:
                    self.notifier_hide = True
                else:#just in case the entry was never created in gconf
                    self.notifier_keep_hidden = False
            else:
                sys.exit(0)

            #listen for gconf keys
            self.specto_gconf.notify_entry("debug_mode", self.key_changed, "debug")

            values = self.watch_io.read_all_watches(True)
            try:
                self.watch_db.create(values)
            except AttributeError, error_fields:
                self.logger.log(_("Could not create a watch, because it is corrupt."), \
                                    "critical", "specto")


            if self.GTK:
                for watch in self.watch_db:
                    self.notifier.add_notifier_entry(watch.id)
                
                #Listen for USR1. If received, answer and show the window
                def listenforUSR1(signum, frame):
                    f = open(self.SPECTO_DIR + "/" + "specto.pid.boot")
                    pid = int(f.readline())
                    f.close()
                    os.kill(pid, signal.SIGUSR1)
                    #If window was not shown, make it appear
                    if not self.notifier.get_state():
                        print _("Showing window, the user ran another instance of specto")
                        self.toggle_notifier()
                    else:
                        print _("Window is already visible! Not doing anything")
                
                signal.signal(signal.SIGUSR1, listenforUSR1)
                
                self.notifier.refresh_all_watches()
            else:
                self.console.start_watches()

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
        """ This is used to set the default settings
        properly the first time Specto is run,
        without using gconf schemas """
        #check if the ekiga sounds exists
        if os.path.exists("/usr/share/sounds/ekiga/voicemail.wav"):
            changed_sound = "/usr/share/sounds/ekiga/voicemail.wav"
        else:
            changed_sound = ""

        self.default_settings = (
            ["always_show_icon", False], #True would be against the HIG!
            ["debug_mode", False],
            ["follow_website_redirects", True],
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
            ["use_keyring", True])
        for default_setting in self.default_settings:
            if self.specto_gconf.get_entry(default_setting[0]) == None:
                self.specto_gconf.set_entry(default_setting[0], \
                                                    default_setting[1])

    def get_version_number(self):
        """Return the Specto version number"""
        version_file_path = (os.path.join(self.util.get_path(category="doc"), "VERSION"))
        version_file = open(version_file_path, 'r')
        version = str(version_file.readline()[:-1])
        version_file.close
        return version

    def check_instance(self):
        """ Check if specto is already running. """
        pidfile = self.SPECTO_DIR + "/" + "specto.pid"
        if not os.path.exists(pidfile):
            f = open(pidfile, "w")
            f.close()
        os.chmod(pidfile, 0600)

        #see if specto is already running
        f = open(pidfile, "r")
        pid = f.readline()
        f.close()
        if pid:
            p = os.system("ps --no-heading --pid " + pid)
            p_name = os.popen("ps -f --pid " + pid).read()
            if p == 0 and "specto" in p_name:
                if self.GTK:
                    #save our pid and prepare a 'pong' system
                    f = open(pidfile + ".boot", "w")
                    f.write(str(os.getpid()))
                    f.close()
                    
                    def notresponding(signum, frame):
                        """ Launch the already running dialog if the
                            other instance doesn't respond """
                        os.unlink(pidfile + ".boot")
                        self.already_running_dialog()
                        
                    def responsereceived(signum, frame):
                        """ Kill this specto if the other one answers """
                        signal.alarm(0)
                        os.unlink(pidfile + ".boot")
                        print _("Specto is already running! The old instance will be brought to front.")
                        sys.exit(0)
                        
                    signal.signal(signal.SIGALRM, notresponding)
                    signal.signal(signal.SIGUSR1, responsereceived)
                    signal.alarm(5)
                    #send signal to raise window
                    os.kill(int(pid), signal.SIGUSR1)
                    
                    #Wait for signals
                    signal.pause()
                    
                    return True
                elif DEBUG:
                    self.logger.log(_("Specto is already running!"), "critical", "specto")
                    sys.exit(0)
                else:
                    print _("Specto is already running!")
                    sys.exit(0)

        #write the pid file
        f = open(pidfile, "w")
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
        It will save the size, position,
        and the last state when you closed Specto.
        """
        #Creating the notifier window, but keeping it hidden
        if self.notifier.get_state() == True and not self.notifier_hide:
            self.specto_gconf.set_entry("show_notifier", True)
            self.notifier.restore_size_and_position()
            self.notifier.notifier.show()
            self.notifier_hide = True
        elif self.notifier.get_state()==True and self.notifier_hide:
            self.notifier.save_size_and_position()
            self.specto_gconf.set_entry("show_notifier", False)
            self.notifier.notifier.hide()
            self.notifier_hide = False
        else:
            self.specto_gconf.set_entry("show_notifier", True)
            self.notifier.restore_size_and_position()
            self.notifier.notifier.show()
            self.notifier_hide = True

    def quit(self, *args):
        """ Save the save and position from the notifier and quit Specto. """
        if self.notifier.get_state() == True and self.notifier_hide:
            self.notifier.save_size_and_position()
        try:
            gtk.main_quit()
        except:
            #create a close dialog
            self.dialog = gtk.Dialog(_("Cannot quit yet"), None, gtk.DIALOG_NO_SEPARATOR | gtk.DIALOG_DESTROY_WITH_PARENT, None)
            self.dialog.set_modal(False)  # Needed to prevent the notifier UI and refresh process from blocking. Also, do not use dialog.run(), because it automatically sets modal to true.

            #HIG tricks
            self.dialog.set_has_separator(False)

            self.dialog.add_button(_("Murder!"), 3)
            self.dialog.add_button(gtk.STOCK_CANCEL, -1)

            self.dialog.label_hbox = gtk.HBox(spacing=6)

            icon = gtk.Image()
            icon.set_from_pixbuf(self.icon_theme.\
                        load_icon("dialog-warning", 64, 0))
            self.dialog.label_hbox.pack_start(icon, True, True, 6)
            icon.show()

            label = gtk.Label(_('<b><big>Specto is currently busy and cannot quit yet.</big></b>\n\nThis may be because it is checking for watch changes.\nHowever, you can try forcing it to quit by clicking the murder button.'))
            label.set_use_markup(True)
            self.dialog.label_hbox.pack_start(label, True, True, 6)
            label.show()

            self.dialog.vbox.pack_start(self.dialog.label_hbox, True, True, 12)
            self.dialog.label_hbox.show()

            icon = gtk.gdk.pixbuf_new_from_file(self.PATH + \
                                'icons/specto_window_icon.svg')
            self.dialog.set_icon(icon)
            self.dialog.connect("delete_event", self.quit_dialog_response)
            self.dialog.connect("response", self.quit_dialog_response)
            self.dialog.show_all()

    def quit_dialog_response(self, widget, answer):
        if answer == 3:
            try:#go figure, it never works!
                self.notifier.stop_refresh = True
                sys.exit(0)
            except:
                #kill the specto process with killall
                os.system('killall specto')
        else:
            self.dialog.hide()
            
    def already_running_dialog(self, *args):
        """ Save the save and position from the notifier and quit Specto. """
        #create a dialog
        self.dialog = gtk.Dialog(_("Error"), None, gtk.DIALOG_NO_SEPARATOR | gtk.DIALOG_DESTROY_WITH_PARENT, None)
        self.dialog.set_modal(False)  # Needed to prevent the notifier UI and refresh process from blocking. Also, do not use dialog.run(), because it automatically sets modal to true.

        #HIG tricks
        self.dialog.set_has_separator(False)

        #self.dialog.add_button(_("Murder!"), 3)
        self.dialog.add_button(gtk.STOCK_OK, 3)

        self.dialog.label_hbox = gtk.HBox(spacing=6)

        icon = gtk.Image()
        icon.set_from_stock(gtk.STOCK_DIALOG_INFO, gtk.ICON_SIZE_DIALOG)
        self.dialog.label_hbox.pack_start(icon, True, True, 6)
        icon.show()

        label = gtk.Label(_('Specto is already running!'))
        label.set_use_markup(True)
        self.dialog.label_hbox.pack_start(label, True, True, 6)
        label.show()

        self.dialog.vbox.pack_start(self.dialog.label_hbox, True, True, 12)
        self.dialog.label_hbox.show()

        icon = gtk.gdk.pixbuf_new_from_file(self.PATH + 'icons/specto_window_icon.svg')
        self.dialog.set_icon(icon)
        self.dialog.connect("delete_event", self.running_dialog_response)
        self.dialog.connect("response", self.running_dialog_response)
        self.dialog.show_all()

    def running_dialog_response(self, widget, answer):
        if answer == 3:
            sys.exit(0)
