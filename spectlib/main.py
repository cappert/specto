#!/usr/bin/env python
# -*- coding: UTF8 -*-

# Specto , Unobtrusive event notifier
#
#       main.py
#
# Copyright (c) 2005-2007, Jean-François Fortin Tam
# This module code is maintained by : Conor Callahan, Jean-François Fortin, Pascal Potvin and Wout Clymans

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

import gobject
import os, sys
from datetime import datetime

import spectlib.util as util
from spectlib.watch import Watch_io
from spectlib.logger import Logger
from spectlib.specto_gconf import GConfClient
from spectlib.i18n import _
from spectlib.import_export import Import_watch

#for the initial ping test
from urllib2 import urlopen
from time import sleep
import time
import thread

#create a gconf object
debug_gconf_client = GConfClient("/apps/specto/preferences")

if debug_gconf_client.get_entry("/debug_mode", "boolean")==True:
    DEBUG = True
elif debug_gconf_client.get_entry("/debug_mode", "boolean")==False:
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
    from spectlib.trayicon import Tray
    from spectlib.notifier import Notifier
    from spectlib.preferences import Preferences
    from spectlib.add_watch import Add_watch
    from spectlib.about import About
    from spectlib.edit_watch import Edit_watch
    from spectlib.logger import Log_dialog
    
class Specto:
    """ The main Specto class. """
    add_w = ""
    edit_w = ""
    error_l = ""
    about = ""
    export = ""

    def __init__(self):
        self.DEBUG = DEBUG
        import gettext #this is for the glade files
        self.glade_gettext = gettext.textdomain("specto")
        self.logger = Logger(self)
        self.check_instance() #see if specto is already running
        self.util = util
        self.PATH = self.util.get_path()
        self.GConfClient = GConfClient
        self.conf_ui = self.GConfClient("/apps/specto/ui")
        self.conf_pref = self.GConfClient("/apps/specto/preferences")
        self.GTK = GTK
        if GTK:
            self.tray = Tray(self)
        self.watch_db = {}
        self.watch_io = Watch_io()
        watch_value_db = self.watch_io.read_options() 
        self.preferences_initialized = False
        self.notifier_initialized = False        
        #listen for gconf keys
        self.conf_pref.notify_entry("/debug_mode", self.key_changed, "debug")

        #basic check for a network connection
        while True:
            try:
                # try if google can be reached, i.e. connection to internet is up
                ping = urlopen('http://www.google.com')
                ping.close()
            except IOError:
                # if not, wait 10 seconds before trying again
                self.logger.log(_("Google.com cannot be reached, your Internet connection seems down! Waiting 10 seconds."), "critical", self.__class__)
                sleep(10)
            else:
                # if yes, start specto
                break

        if GTK:
            if self.conf_pref.get_entry("/always_show_icon", "boolean") == False:
                #if the user has not requested the tray icon to be shown at all times, it's impossible that the notifier is hidden on startup, so we must show it.
                self.notifier_keep_hidden = False
                self.toggle_notifier()
            elif self.conf_ui.get_entry("/notifier_state", "boolean")==True:
                self.notifier_keep_hidden = False
                self.toggle_notifier()
            elif self.conf_ui.get_entry("/notifier_state", "boolean")==False:
                self.notifier_keep_hidden = True
                self.toggle_notifier()
                self.notifier_keep_hidden = False
            else:#just in case the entry was never created in gconf
                self.notifier_keep_hidden = False
                self.toggle_notifier()
                
        self.create_all_watches(watch_value_db)
        
        if GTK:
            gtk.main()
        else:
            self.go = gobject.MainLoop()
            self.go.run()
            
    def key_changed(self, *args):
        """ Listen for gconf keys. """
        label = args[3]
        conf_pref = self.GConfClient("/apps/specto/preferences")
        
        if label == "debug":
            self.DEBUG = conf_pref.get_entry("/debug_mode", "boolean")
            
    def check_instance(self):
        """ Check if specto is already running. """
        pidfile = os.environ['HOME'] + "/.specto/" + "specto.pid"
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

    def recreate_tray(self, *args):
        """
        Recreate a tray icon if the notification area unexpectedly quits.
        """
        try:self.tray.destroy()
        except:pass
        self.tray = ""
        self.tray = Tray(self)
        self.count_updated_watches()

    def create_all_watches(self, value_db):
        """
        Create the watches at startup.
        """
        for i in value_db:
            self.create_watch(value_db[i])
            if GTK:
                while gtk.events_pending():
                    gtk.main_iteration_do(False)
                    
        if self.conf_ui.get_entry("/display_all", "boolean") == False:
            self.notifier.wTree.get_widget("display_all_watches").set_active(False)
            self.notifier.toggle_display_all_watches()
        
        #start the active watches
        if self.notifier_initialized:            
            self.notifier.refresh()
            
    def create_watch(self, values):
        """ Add a watch to the watches repository. """
        id = len(self.watch_db)
        
        if values['type'] == 0: #add a website
            from spectlib.watch_web_static import Web_watch
            self.watch_db[id] = Web_watch(self, values['name'], values['refresh'], values['uri'], id, values['error_margin']) #TODO: Authentication

        elif values['type'] == 1: #add an email
            if int(values['prot']) == 0: #check if pop3, imap or gmail is used
                import spectlib.watch_mail_pop3
                self.watch_db[id] = spectlib.watch_mail_pop3.Mail_watch(values['refresh'], values['host'], values['username'], values['password'], values['ssl'], self, id, values['name'])

            elif int(values['prot']) == 1:
                import spectlib.watch_mail_imap
                self.watch_db[id] = spectlib.watch_mail_imap.Mail_watch(values['refresh'], values['host'], values['username'], values['password'], values['ssl'], self, id, values['name'])
            else:
                import spectlib.watch_mail_gmail
                self.watch_db[id] = spectlib.watch_mail_gmail.Mail_watch(values['refresh'], values['username'], values['password'], self, id, values['name'])

        elif values['type'] == 2: #add a file
            from spectlib.watch_file import File_watch
            self.watch_db[id] = File_watch(values['refresh'], values['file'], values['mode'], self, id, values['name'])
            
        elif values['type'] == 3: #add a process watch
            from spectlib.watch_process import Process_watch
            self.watch_db[id] = Process_watch(values['refresh'], values['process'], self, id, values['name'])
            
            
        
        try:
            self.watch_db[id].updated = values['updated']
        except:
            self.watch_db[id].updated = False
            
        try:
            self.watch_db[id].active = values['active']
        except:
            self.watch_db[id].active = True
        
        try:
            self.watch_db[id].last_updated = values['last_updated']
        except:
            self.watch_db[id].last_updated = _("No updates yet.")
            
        if GTK:
            if not self.notifier_initialized:
                self.notifier = Notifier(self)
                self.notifier.restore_size_and_position()#fixme: is this necessary? this makes specto output stuff for nothing.
            self.notifier.add_notifier_entry(values['name'], values['type'], id)
            try:
                if values['updated']:
                    self.toggle_updated(id)
            except:
                pass
                
            try:
                if values['active'] == False:
                    self.notifier.deactivate(id)
            except:
                pass
                
        return id
    
    def clear_watch(self, id):
        """ Mark a watch as not updated. """
        new_values = {}
        self.watch_db[id].updated = False
        new_values['name'] = self.watch_db[id].name
        new_values['updated'] = False
        self.watch_io.write_options(new_values)
    
        self.count_updated_watches()
        
    def update_watch(self, progress, id):
        """ Display a refresh icon when updating watches. """
        self.notifier.toggle_updating(progress, id)

    def set_status(self, id, status):
        """ Set the status from a watch (active/not active). """
        new_values = {}
        new_values['name'] = self.watch_db[id].name
        new_values['active'] = status
        if status == False:
            new_values['updated'] = False
            self.watch_db[id].updated = False
            self.notifier.clear_watch('',id)
        self.watch_db[id].active = status
        self.watch_io.write_options(new_values)
            
    def replace_name(self, orig, new):
        """ Replace the name from a watch in watches.list. """
        self.watch_io.replace_name(orig, new)

    def start_watch(self, id):
        """ Start a watch. """
        self.notifier.toggle_updating(True, id)
        self.watch_db[id].start_watch()
        self.logger.log(_("watch \"%s\" started") % self.watch_db[id].name, "info", self.__class__)

    def stop_watch(self, id):
        """ Stop a watch. """
        self.watch_db[id].stop_watch()
        self.logger.log(_("watch \"%s\" stopped") % self.watch_db[id].name, "info", self.__class__)

    def add_watch(self, values):
        """ Add a new watch. """
        new_values = {}
        new_values['name'] = values['name']
        new_values['type'] = values['type']
        new_values['refresh'] = self.set_interval(values['refresh_value'], values['refresh_unit'])

        if int(values['type']) == 0: #web
            new_values['uri'] = values['url']
            new_values['error_margin'] = values['error_margin']

        elif int(values['type']) == 1: #mail
            if int(values['prot']) == 0 or int(values['prot']) == 1:
                new_values['host'] = values['host']
                new_values['ssl'] = values['ssl']

            new_values['username'] = values['username']
            new_values['password'] = values['password']
            new_values['prot'] = values['prot']
        
        elif int(values['type']) == 2: #file
            new_values['file'] = values['file']
            new_values['mode'] = values['mode']
            
        elif int(values['type']) == 3: #process
            new_values['process'] = values['process']

        id = self.create_watch(new_values)
        self.start_watch(id)

        self.watch_io.write_options(new_values)
        
    def edit_watch(self, values):
        """ Edit a watch. """
        new_values = {}
        new_values['name'] = values['name']
        new_values['type'] = values['type']
        new_values['refresh'] = self.set_interval(values['refresh_value'], values['refresh_unit'])

        if int(values['type']) == 0: #web
            new_values['uri'] = values['url']
            new_values['error_margin'] = values['error_margin']

        elif int(values['type']) == 1: #mail
            if int(values['prot']) != 2: #gmail doesn't need a host and SSL it seems, so this is updated only of it's another kind of mail watch
                new_values['host'] = values['host']
                new_values['ssl'] = values['ssl']
                
            new_values['username'] = values['username']
            new_values['password'] = values['password']
            new_values['prot'] = values['prot']
        
        elif int(values['type']) == 2: #file
            new_values['file'] = values['file']

        self.watch_io.write_options(new_values)
        self.notifier.show_watch_info()

    def remove_watch(self, name, id):
        """ Remove a watch. """
        try:
            self.stop_watch(id)
        except:
            pass
        del self.watch_db[id]
        self.count_updated_watches()
        self.watch_io.remove_watch(name)#do not clear the watch after removing it or it will mess up the watches.list
        self.notifier.model.remove(self.notifier.iter[id])
        
    def check_unique_watch(self, name):
        """ Check if the watch name is unique. """
        if self.watch_io.search_watch(name) and GTK:
            return False
        else:
            return True
        
    def count_updated_watches(self):
        """ Count the number of updated watches for the tooltip. """
        tooltip_updated_watches = { 0:0,1:0,2:0,3:0 }
        for i in self.watch_db:
            if self.watch_db[i].updated == True:
                self.tray.set_icon_state_excited()#change the tray icon color to orange
                tooltip_updated_watches[self.watch_db[i].type] = tooltip_updated_watches[self.watch_db[i].type] + 1
        if tooltip_updated_watches.values() == [0,0,0,0]:#there are no more watches to clear, reset the tray icon
            self.tray.set_icon_state_normal()
            self.notifier.wTree.get_widget("button_clear_all").set_sensitive(False)

        self.tray.show_tooltip(tooltip_updated_watches)

    def toggle_updated(self, id):
        """
        When a watch is updated: change name in notifier window,
        change the tray icon state, play a sound, ...
        """
        new_values = {}
        now = datetime.today()
        
        #TODO:XXX:GETTEXT
        new_values['last_updated'] = now.strftime("%A %d %b %Y %H:%M")
        self.watch_db[id].last_updated = now.strftime("%A %d %b %Y %H:%M")
        
        self.watch_db[id].updated = True
        
        if self.notifier_initialized: self.notifier.toggle_updated(id)
        new_values['name'] = self.watch_db[id].name
        new_values['updated'] = True 
        self.watch_io.write_options(new_values) #write the watches state in watches.list
        
        self.count_updated_watches() #show the tooltip
        
    def toggle_all_cleared(self):
        """ Set the state from all the watches back to 'not updated'. """
        for i in self.watch_db:
            new_values = {}
            self.watch_db[i].updated = False
            new_values['name'] = self.watch_db[i].name
            new_values['updated'] = False
            self.watch_io.write_options(new_values)
            
        self.count_updated_watches()

    def set_interval(self, refresh, refresh_unit):
        """
        Set the interval between the update checks.
        refresh = number
        refresh_unit = days, hours, minutes,... in values of 0, 1, 2, 3.
        """
        new_refresh = 0
        if refresh_unit == 0:#seconds
            new_refresh = refresh * 1000
        elif refresh_unit == 1:#minutes
            new_refresh = refresh * 60 * 1000
        elif refresh_unit == 2:#hours
            new_refresh = (refresh * 60) * 60 * 1000
        elif refresh_unit == 3:#days
            new_refresh = ((refresh * 60) * 60) * 24 *1000
        
        return new_refresh
        
    def get_interval(self, value):
        """ Get the interval between 2 updates. """
        if ((value / 60) / 60) / 24 / 1000 > 0:
            refresh_value = ((value / 60) / 60) / 24 / 1000
            type = 3
        elif (value / 60) / 60 / 1000 > 0:
            refresh_value = (value / 60) / 60 / 1000
            type = 2
        elif value / 60 / 1000 > 0:
            refresh_value = value / 60 / 1000
            type = 1
        else:
            refresh_value = value / 1000
            type = 0
            
        return refresh_value, type

    def toggle_notifier(self, *args):
        """
        Toggle the state of the notifier, hidden or shown.
        It will save the size, position, and the last state when you closed Specto.
        """
        #Creating the notifier window, but keeping it hidden
        if not self.notifier_initialized and self.notifier_keep_hidden:
            self.notifier = Notifier(self)
            self.notifier.restore_size_and_position()
            self.notifier.notifier.hide()            
        #Creating the notifier window and displaying it
        elif not self.notifier_initialized and not self.notifier_keep_hidden:
            self.notifier = Notifier(self)
            self.notifier.restore_size_and_position()
            self.notifier.notifier.show()

        elif self.notifier_initialized:
            if self.notifier.get_state()==True and self.notifier_keep_hidden:
                self.logger.log(_("notifier: reappear"), "debug", self.__class__)
                self.conf_ui.set_entry("/notifier_state", True, "boolean")
                self.notifier.restore_size_and_position()
                self.notifier.notifier.show()
            elif self.notifier.get_state()==True and not self.notifier_keep_hidden:
                self.logger.log(_("notifier: hide"), "debug", self.__class__)
                self.conf_ui.set_entry("/notifier_state", False, "boolean")
                self.notifier.notifier.hide()
            else:
                self.logger.log(_("notifier: reappear"), "debug", self.__class__)
                self.conf_ui.set_entry("/notifier_state", True, "boolean")
                self.notifier.restore_size_and_position()
                self.notifier.notifier.show()
        self.notifier_initialized = True

    def show_preferences(self, *args):
        """ Show the preferences window. """
        if not self.preferences_initialized or self.preferences.get_state() == True:
            self.logger.log(_("preferences: create"), "debug", self.__class__)
            self.pref=Preferences(self)
        else:
            self.logger.log(_("preferences: reappear"), "debug", self.__class__)
            self.pref.show()
            
    def show_error_log(self, *args):
        """ Show the error log. """
        if self.error_l == "":
            self.error_l= Log_dialog(self)
            self.logger.log(_("error log: create"), "debug", self.__class__)
        elif self.error_l.log_dialog.flags() & gtk.MAPPED:
            self.logger.log(_("error log: already visible"), "debug", self.__class__)
        else:
            self.error_l= Log_dialog(self)
            self.logger.log(_("error log: recreate"), "debug", self.__class__)
                    
    def show_add_watch(self, *args):
        """ Show the add watch window. """
        if self.add_w == "":
            self.add_w= Add_watch(self)
            self.logger.log(_("add watch: create"), "debug", self.__class__)
        elif self.add_w.add_watch.flags() & gtk.MAPPED:
            self.logger.log(_("add watch: already visible"), "debug", self.__class__)
        else:
            self.add_w= Add_watch(self)
            self.logger.log(_("add watch: recreate"), "debug", self.__class__)

    def show_edit_watch(self, id, *args):
        """ Show the edit watch window. """
        selected = ""
        if not id == -1:
            selected = self.watch_db[id]
        else:
            for i in self.watch_db:
                if self.watch_db[i].name == args[0]:
                    selected = self.watch_db[i]

        if self.edit_w == "":
            self.edit_w= Edit_watch(self, selected)
            self.logger.log(_("edit watch: create"), "debug", self.__class__)
        elif self.edit_w.edit_watch.flags() & gtk.MAPPED:
            self.logger.log(_("edit watch: already visible"), "debug", self.__class__)
        else:
            self.edit_w= Edit_watch(self, selected)
            self.logger.log(_("edit watch: recreate"), "debug", self.__class__)

    def show_about(self, *args):
        """ Show the about window. """
        if self.about == "":
            self.about = About(self)
        elif self.about.about.flags() & gtk.MAPPED:
            pass
        else:
            self.about = About(self)
            
    def show_help(self, *args):
        """ Show the help web page. """
        self.util.show_webpage("http://specto.ecchi.ca")
        
    def import_export_watches(self, action):
        """ Show the import/export window. """
        if self.export == "":
            self.export = Import_watch(self, action)
        elif self.export.import_watch.flags() & gtk.MAPPED:
            pass
        else:
            self.export = Import_watch(self, action)        
       
    def quit(self, *args):
        """ Save the save and position from the notifier and quit Specto. """
        if self.notifier.get_state()==True and not self.notifier_keep_hidden:
            self.notifier.save_size_and_position()#when quitting specto abruptly, remember the notifier window properties
        try:
            gtk.main_quit()
        except:
            self.notifier.stop_refresh = True
            #create a close dialog
            dialog = gtk.Dialog("Error quitting specto", None, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, None)
            dialog.add_button(gtk.STOCK_CANCEL, -1)
            dialog.add_button(_("Murder!"), 3)            
            label = gtk.Label(_('Specto is currently busy and cannot quit yet.\n\nThis may be because it is checking for watch updates.\nHowever, you can try forcing it to quit by clicking the murder button.'))
            dialog.vbox.pack_start(label, True, True, 20)
            label.show()
            icon = gtk.gdk.pixbuf_new_from_file(self.PATH + 'icons/specto_window_icon.png' )
            dialog.set_icon(icon)
            answer = dialog.run()
            if answer == 3:
                try:
                    sys.exit(0)
                except:
                    #kill the specto process with killall
                    os.system('killall specto')
            else:
                dialog.destroy()
