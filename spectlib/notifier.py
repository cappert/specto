# -*- coding: UTF8 -*-

# Specto , Unobtrusive event notifier
#
#       notifier.py
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

import sys
import spectlib.edit_watch
import spectlib.util
from random import randrange
from spectlib.i18n import _
try:
    import pygtk
    pygtk.require("2.0")
except:
    pass

try:
    import gtk
    import gtk.glade
    import gobject
    import pango
except:
    pass
    
    
class Notifier:
    """
    Class to create the main specto window
    """
    
    def __init__(self, specto):
        """
        In this init we are going to display the main notifier window.
        """
        self.specto = specto
        self.iter = {}
        self.watches = 0
        #create tree
        gladefile= self.specto.PATH + 'glade/notifier.glade' 
        windowname= "notifier"
        self.wTree=gtk.glade.XML(gladefile,windowname, self.specto.glade_gettext)
        self.model = gtk.ListStore(gobject.TYPE_BOOLEAN, gtk.gdk.Pixbuf, gobject.TYPE_STRING, gobject.TYPE_INT, gobject.TYPE_INT, pango.Weight)
        #__icon_size  = gtk.icon_size_lookup (gtk.ICON_SIZE_BUTTON) [0] #needed, otherwise gtk.image will not take into account the icon size no matter what you specify. ###uh no, it's not, actually it was a gnome-icon-theme 2.17 bug. I guess this line should be removed.
        #catch some events
        dic= {
        "on_add_activate": self.show_add_watch,
        "on_edit_activate": self.show_edit_watch,
        "on_clear_all_activate": self.clear_all,
        "on_preferences_activate": self.show_preferences,
        "on_refresh_activate": self.refresh,
        "on_close_activate": self.delete_event,
        "on_import_watches_activate": self.import_watches,
        "on_export_watches_activate": self.export_watches,
        "on_error_log_activate": self.show_error_log,
        "on_display_all_watches_activate": self.toggle_show_deactivated_watches,
        "on_display_toolbar_activate": self.toggle_display_toolbar,
        "on_help_activate": self.show_help,
        "on_about_activate": self.show_about,
        "on_treeview_row_activated": self.open_watch_callback,
        "on_btnOpen_clicked": self.open_watch_callback,
        "on_btnClear_clicked": self.clear_watch,
        "on_treeview_cursor_changed": self.show_watch_info,
        "on_btnEdit_clicked": self.show_edit_watch, 
        "on_by_watch_type_activate": self.sort_type,
        "on_by_name_activate": self.sort_name,
        "on_by_watch_active_activate": self.sort_active
        }
        self.wTree.signal_autoconnect(dic)

        self.notifier=self.wTree.get_widget("notifier")
        icon = gtk.gdk.pixbuf_new_from_file(self.specto.PATH + 'icons/specto_window_icon.svg' )
        self.notifier.set_icon(icon)
        
        #create the gui
        self.create_notifier_gui()

        self.pref = ""
        self.add_w = ""
        self.edit_w = ""
        self.stop_refresh = False
        

### Watch functions ###
                
    def clear_watch(self, widget, *id):
        """
        Call the main function to clear the watch and reset the name in the notifier.
        If widget == '' then id will be used to clear the watch else the selected watch will be cleared.
        """
        if widget:
            model, iter = self.treeview.get_selection().get_selected()
            id = int(model.get_value(iter, 3))
        else:
            id = id[0]
            
        type = self.specto.watch_db[id].type
        self.specto.clear_watch(id)
        self.model.set(self.iter[id], 2, self.specto.watch_db[id].name, 5, pango.WEIGHT_NORMAL)
        
        icon = self.specto.icon_theme.load_icon("error", 22, 0)
        if type == 0:#website
            icon = self.specto.icon_theme.load_icon("applications-internet", 22, 0)
        elif type == 1:#email
            icon = self.specto.icon_theme.load_icon("emblem-mail", 22, 0)
        elif type == 2:#file/folder
            icon = self.specto.icon_theme.load_icon("folder", 22, 0)
        elif type == 3:#system process
            icon = self.specto.icon_theme.load_icon("applications-system", 22, 0)
        elif type == 4:#port
            icon = self.specto.icon_theme.load_icon("network-transmit-receive", 22, 0)
        
        if self.model.iter_is_valid(self.iter[id]):
            self.model.set_value(self.iter[id], 1, self.make_transparent(icon, 50))
        
        if self.specto.watch_db[id].updated == False:
            self.wTree.get_widget("btnClear").set_sensitive(False)
        else:
            self.wTree.get_widget("btnClear").set_sensitive(True)

    def clear_all(self, widget):
        """ Call the main function to clear all watches and reset the name in the notifier. """
        self.specto.toggle_all_cleared()
        self.wTree.get_widget("btnClear").set_sensitive(False)
        self.wTree.get_widget("button_clear_all").set_sensitive(False)
        self.wTree.get_widget("clear_all1").set_sensitive(False)
        
        icon = self.specto.icon_theme.load_icon("error", 22, 0)
        for i in self.specto.watch_db:
            if self.model.iter_is_valid(self.iter[i]):
                self.model.set(self.iter[i], 2, "%s" % self.specto.watch_db[i].name, 5, pango.WEIGHT_NORMAL)
                type = self.specto.watch_db[i].type

                icon = self.specto.icon_theme.load_icon("error", 22, 0)
                if type == 0:#website
                    icon = self.specto.icon_theme.load_icon("applications-internet", 22, 0)
                elif type == 1:#email
                    icon = self.specto.icon_theme.load_icon("emblem-mail", 22, 0)
                elif type == 2:#file/folder
                    icon = self.specto.icon_theme.load_icon("folder", 22, 0)
                elif type == 3:#system process
                    icon = self.specto.icon_theme.load_icon("applications-system", 22, 0)
                elif type == 4:#port
                    icon = self.specto.icon_theme.load_icon("network-transmit-receive", 22, 0)
                self.model.set_value(self.iter[i], 1, self.make_transparent(icon, 50))

    def refresh(self, *widget):
        """ Call the main funcion to refresh all active watches and change refresh icon to stop. """
        if self.wTree.get_widget("button_refresh").get_stock_id() == "gtk-refresh":
            self.wTree.get_widget("button_refresh").set_stock_id("gtk-stop") #menu item, does not allow changing label
            self.wTree.get_widget("button_add").set_sensitive(False)
            self.wTree.get_widget("btnEdit").set_sensitive(False)
            for i in self.iter:
                if self.stop_refresh == True:
                    self.stop_refresh = False
                    break
                
                try:
                    iter = self.model.get_iter(i)
                    if self.model.iter_is_valid(iter):
                        model = self.model
                        id = int(model.get_value(iter, 3))
                except:
                    break

                if self.specto.watch_db[id].active == True:
                    try:
                        self.specto.stop_watch(id)
                    except:
                        pass
                    self.specto.start_watch(id)    
                    
                if self.specto.GTK:
                    while gtk.events_pending():
                        gtk.main_iteration_do(False)
            self.wTree.get_widget("button_refresh").set_stock_id("gtk-refresh") #menu item, does not allow changing label
            self.wTree.get_widget("button_add").set_sensitive(True) 
            self.wTree.get_widget("btnEdit").set_sensitive(True)           
        else:
            self.stop_refresh = True    
                
    def import_watches(self, *widget):
        self.specto.import_export_watches(True)
        
    def export_watches(self, *widget):
        self.specto.import_export_watches(False)

    def toggle_updated(self, id):
        """ Change the name and icon from the watch in the notifier window. """
        self.model.set(self.iter[id], 2, "%s" % self.specto.watch_db[id].name, 5, pango.WEIGHT_BOLD)
        self.wTree.get_widget("button_clear_all").set_sensitive(True)
        self.wTree.get_widget("clear_all1").set_sensitive(True)

        type = self.specto.watch_db[id].type
        icon = self.specto.icon_theme.load_icon("error", 22, 0)
        if type == 0:#website
            icon = self.specto.icon_theme.load_icon("applications-internet", 22, 0)
        elif type == 1:#email
            icon = self.specto.icon_theme.load_icon("emblem-mail", 22, 0)
        elif type == 2:#file/folder
            icon = self.specto.icon_theme.load_icon("folder", 22, 0)
        elif type == 3:#system process
            icon = self.specto.icon_theme.load_icon("applications-system", 22, 0)
        elif type == 4:#port
            icon = self.specto.icon_theme.load_icon("network-transmit-receive", 22, 0)
        if self.model.iter_is_valid(self.iter[id]):
            self.model.set_value(self.iter[id], 1, self.make_transparent(icon, 0))
        
        if self.treeview.get_selection().get_selected():
            model, iter = self.treeview.get_selection().get_selected()
            if iter != None:
                i = int(model.get_value(iter, 3))
                if self.specto.watch_db[i].name == self.specto.watch_db[id].name:
                    self.show_watch_info()
                    
    def toggle_updating(self,progress, id):
        """ If progress is True, a refresh icon is shown, else the type icon is shown. """ 
        icon = self.specto.icon_theme.load_icon("error", 22, 0)
        if progress == True:
            icon = self.specto.icon_theme.load_icon("reload", 22, 0)
            self.model.set_value(self.iter[id], 1, icon) #do not use transparency here, it's useless and dangerous
            if self.specto.GTK:
                while gtk.events_pending():#this is to refresh the UI and display the "refresh" icon properly. It works! :)
                    gtk.main_iteration_do(False)
        else:
            if self.specto.watch_db[id].error == True:
                icon = self.specto.icon_theme.load_icon("error", 22, 0)
            else:
                type = self.specto.watch_db[id].type
                icon = self.specto.icon_theme.load_icon("error", 22, 0)
                if type == 0:#website
                    icon = self.specto.icon_theme.load_icon("applications-internet", 22, 0)
                elif type == 1:#email
                    icon = self.specto.icon_theme.load_icon("emblem-mail", 22, 0)
                elif type == 2:#file/folder
                    icon = self.specto.icon_theme.load_icon("folder", 22, 0)
                elif type == 3:#system process
                    icon = self.specto.icon_theme.load_icon("applications-system", 22, 0)
                elif type == 4:#port
                    icon = self.specto.icon_theme.load_icon("network-transmit-receive", 22, 0)
            if self.model.iter_is_valid(self.iter[id]):
                if self.specto.watch_db[id].updated == False:
                    self.model.set_value(self.iter[id], 1, self.make_transparent(icon, 50))#we must keep it faded, exceptionally
                else:
                    #self.model.set_value(self.iter[id], 1, self.make_transparent(icon, 0)) #do not use transparency here, it's useless and dangerous
                    self.model.set_value(self.iter[id], 1, icon)
        
    def deactivate(self, id):
        """ Disable the checkbox from the watch. """
        self.model.set_value(self.iter[id], 0, 0)#TODO: make the text label in the "Name" column and the buttons insensitive
        
    def make_transparent(self, pixbuf, percent):
        """ Calculate the alpha and return a transparent pixbuf. The input percentage is the 'transparency' percentage. 0 means no transparency. """
        pixbuf = pixbuf.add_alpha(False, '0', '0', '0')
        for row in pixbuf.get_pixels_array():
            for pix in row:
                pix[3] = min(int(pix[3]), 255 - (percent * 0.01 * 255))#note: we must *0.01, NOT /100, otherwise it won't work
        return pixbuf
            
    def add_notifier_entry(self, name, type, id):
        """ Add an entry to the notifier list. """
        i = id

        icon = self.specto.icon_theme.load_icon("error", 22, 0)
        if type == 0:#website
            icon = self.specto.icon_theme.load_icon("applications-internet", 22, 0)
        elif type == 1:#email
            icon = self.specto.icon_theme.load_icon("emblem-mail", 22, 0)
        elif type == 2:#file/folder
            icon = self.specto.icon_theme.load_icon("folder", 22, 0)
        elif type == 3:#system process
            icon = self.specto.icon_theme.load_icon("applications-system", 22, 0)
        elif type == 4:#port
            icon = self.specto.icon_theme.load_icon("network-transmit-receive", 22, 0)
        
        self.iter[i] = self.model.insert_before(None, None)
        self.model.set_value(self.iter[i], 0, 1)
        self.model.set_value(self.iter[i], 1, self.make_transparent(icon, 50))
        self.model.set_value(self.iter[i], 2, name)
        self.model.set_value(self.iter[i], 3, id)
        self.model.set_value(self.iter[i], 4, type)
        self.model.set(self.iter[i], 5, pango.WEIGHT_NORMAL)#make sure the text is not fuzzy on startup
        self.watches = self.watches + 1
        
    def check_clicked(self, object, path, model):
        """ Call the main function to start/stop the selected watch. """
        sel = self.treeview.get_selection()
        sel.select_path(path)
            
        model, iter = self.treeview.get_selection().get_selected()
        i = int(model.get_value(iter, 3))
        
        if model.get_value(iter,0):
            model.set_value(iter, 0, 0)
            self.specto.stop_watch(i)
        else:
            model.set_value(iter, 0, 1)
            self.specto.start_watch(i)
            
        self.specto.set_status(i, model.get_value(iter, 0))
        
        if self.wTree.get_widget("display_all_watches").active == False:
            model.remove(iter)

    def connected_message(self, connected):
        if not connected:
            self.wTree.get_widget("statusbar1").push(0, _("The network connection seems to be down, watches will not update until then."))
            self.wTree.get_widget("statusbar1").show()
        else:
            self.wTree.get_widget("statusbar1").hide()

    def show_watch_info(self, *args):
        """ Show the watch information in the notifier window. """
        model, iter = self.treeview.get_selection().get_selected()
        
        if iter != None and self.model.iter_is_valid(iter):
            self.wTree.get_widget("edit").set_sensitive(True)

            #hide the tip of the day and show the buttons
            self.lblTip.hide()
            self.wTree.get_widget("vbox_panel_buttons").show()

            #hide all the tables
            self.notebook_info.hide()
            
            id = int(model.get_value(iter, 3))
        
            selected = self.specto.watch_db[id]
        
            if selected.updated == False:
                self.wTree.get_widget("btnClear").set_sensitive(False)
            else:
                self.wTree.get_widget("btnClear").set_sensitive(True)

            #show the table
            self.notebook_info.show()
            self.notebook_info.set_current_page(selected.type)

            if selected.type == 0:
                #get the info
                self.wTree.get_widget("lblNameText").set_label(selected.name)
                self.wTree.get_widget("lblLocationText").set_label(selected.url_)

                margin = float(selected.error_margin) * 100
                self.wTree.get_widget("lblErrorMarginText").set_label(str(margin) + " %")

                self.wTree.get_widget("lblLastUpdateText").set_label(selected.last_updated)

                #show the image
                self.wTree.get_widget("imgWatch").set_from_pixbuf(self.specto.icon_theme.load_icon("applications-internet", 64, 0))

            elif selected.type == 1:
                #get the info
                self.wTree.get_widget("lblMailNameText").set_label(selected.name)

                if selected.prot == 2:
                    self.wTree.get_widget("lblMailHostText").set_label( _("gmail <i>(%s unread)</i>") % selected.oldMsg )
                else:
                    self.wTree.get_widget("lblMailHostText").set_label(selected.host)

                self.wTree.get_widget("lblMailUsernameText").set_label(selected.user)
                self.wTree.get_widget("lblMailLastUpdateText").set_label(selected.last_updated)

                #show the image
                self.wTree.get_widget("imgWatch").set_from_pixbuf(self.specto.icon_theme.load_icon("emblem-mail", 64, 0))
                
            elif selected.type == 2:
                self.wTree.get_widget("lblFileNameText").set_label(selected.name)
                self.wTree.get_widget("lblFileName").set_label(selected.file)
                self.wTree.get_widget("lblFileLastUpdateText").set_label(selected.last_updated)
                self.wTree.get_widget("imgWatch").set_from_pixbuf(self.specto.icon_theme.load_icon("folder", 64, 0))
                
            elif selected.type == 3:
                self.wTree.get_widget("lblProcessNameText").set_label(selected.name)
                self.wTree.get_widget("lblProcessName").set_label(selected.process)
                self.wTree.get_widget("lblProcessLastUpdateText").set_label(selected.last_updated)
                self.wTree.get_widget("imgWatch").set_from_pixbuf(self.specto.icon_theme.load_icon("applications-system", 64, 0))

            elif selected.type == 4:
                self.wTree.get_widget("lblPortNameText").set_label(selected.name)
                self.wTree.get_widget("lblPortName").set_label(selected.port)
                self.wTree.get_widget("lblPortLastUpdateText").set_label(selected.last_updated)
                self.wTree.get_widget("imgWatch").set_from_pixbuf(self.specto.icon_theme.load_icon("network-transmit-receive", 64, 0))
                
        else:
            self.wTree.get_widget("edit").set_sensitive(False)

            #hide the tip of the day and show the buttons
            self.lblTip.show()
            self.wTree.get_widget("vbox_panel_buttons").hide()

            #hide all the tables
            self.notebook_info.hide()
            
    def open_watch(self, id):
        """ 
        Open the selected watch. 
        Returns False if the watch failed to open
        """
        res = True
        selected = self.specto.watch_db[id]
        self.specto.logger.log(_("watch \"%s\" opened") % self.specto.watch_db[id].name, "info", self.__class__)
        if selected.type == 0:
            uri_real = self.specto.watch_io.read_option(self.specto.watch_db[id].name, "uri_real")#this is just in case the uri_real parameter is present, i.e.: a web feed
            if uri_real:
                spectlib.util.show_webpage(uri_real)
            else:
                spectlib.util.show_webpage(selected.url_)
        elif selected.type == 1:
            if selected.prot == 2: #gmail opens in a browser
                spectlib.util.show_webpage("https://gmail.google.com")
            else:
                spectlib.util.open_gconf_application("/desktop/gnome/url-handlers/mailto")
        elif selected.type == 2:
            spectlib.util.open_file_watch(selected.file)
        else: 
            res=False
        return res

    def open_watch_callback(self, *args):
        """
        Opens the selected watch and mark it is not updated anymore
        """
        model, iter = self.treeview.get_selection().get_selected()
        id = int(model.get_value(iter, 3))
        if self.open_watch(id):
            self.clear_watch(args[0])

                
    def change_entry_name(self, *args):
        """ Edit the name from the watch in the notifier window. """
        #change the name in the treeview
        model, iter = self.treeview.get_selection().get_selected()
        id = int(model.get_value(iter, 3))
        self.change_name(args[2], id)
        
    def change_name(self, new_name, id):
        if self.specto.watch_db[id].updated == True:
            weight = pango.WEIGHT_BOLD
        else:
            weight = pango.WEIGHT_NORMAL
        self.model.set(self.iter[id], 2, new_name, 5, weight)
        
        #write the new name in watches.list
        self.specto.replace_name(self.specto.watch_db[id].name, new_name)
        #change the name in the database
        self.specto.watch_db[id].set_name(new_name)
        self.show_watch_info()
        
### GUI FUNCTIONS ###

    def get_quick_tip(self):#these are the tips of the day that are shown on startup. The code that displays them is further below.
        tips = [_("You can add all kinds of websites as watches. Static pages, RSS or Atom feeds, etc. Specto will automatically handle them."), 
                    _("Website watches can use an error margin that allows you to set a minimum difference percentage. This allows you to adapt to websites that change constantly or have lots of advertising."),
                    _("Single-click an existing watch to display information, and double-click it to open the content."),
                    _("Please set a reasonable refresh interval in order to save bandwidth and prevent you from being blocked from content providers.")
                    ]
        chosen_tip = tips[randrange(len(tips))]
        return chosen_tip
        
    def toggle_display_toolbar(self, *args):
        """ Show or hide the toolbar. """
        if self.wTree.get_widget("display_toolbar").active:
            self.wTree.get_widget("toolbar").show()
            self.specto.specto_gconf.set_entry("hide_toolbar", False)
        else:
            self.wTree.get_widget("toolbar").hide()
            self.specto.specto_gconf.set_entry("hide_toolbar", True)
            
    def toggle_show_deactivated_watches(self, startup=False): #, *widget):
        """ Display only active watches or all watches. """
        if startup !=True: startup=False #this is important to prevent *widget from messing with us. If you don't believe me, print startup ;)
        if self.wTree.get_widget("display_all_watches").active:
            for id in self.specto.watch_db:
                if self.specto.watch_db[id].active ==False:#for each watch that is supposed to be inactive, show it in the notifier but don't activate it
                    if startup==False:#recreate the item because it was deleted
                        self.add_notifier_entry(self.specto.watch_db[id].name, self.specto.watch_db[id].type, id)
                    self.deactivate(id)
            self.specto.specto_gconf.set_entry("show_deactivated_watches", True)
        else:#hide the deactivated watches
            for i in self.iter:
                if self.model.iter_is_valid(self.iter[i]):
                    path = self.model.get_path(self.iter[i])
                    iter = self.model.get_iter(path)
                    model = self.model
                    id = int(model.get_value(iter, 3))

                    if self.specto.watch_db[id].active == False:
                        model.remove(iter)
            self.specto.specto_gconf.set_entry("show_deactivated_watches", False)

    def delete_event(self, *args):
        """
        Return False to destroy the main window.
        Return True to stop destroying the main window.
        """
        self.save_size_and_position()
        if self.specto.specto_gconf.get_entry("always_show_icon") == True:
            self.notifier.hide()
            self.specto.specto_gconf.set_entry("show_notifier", False)#save the window state for the next time specto starts
            return True
        else:
            self.specto.quit()

    def restore_size_and_position(self):
        """
        Restore the size and the postition from the notifier window.
        """
        saved_window_width = self.specto.specto_gconf.get_entry("window_notifier_width")
        saved_window_height = self.specto.specto_gconf.get_entry("window_notifier_height")
        saved_window_x = self.specto.specto_gconf.get_entry("window_notifier_x")
        saved_window_y = self.specto.specto_gconf.get_entry("window_notifier_y")
        if self.specto.specto_gconf.get_entry("hide_from_windowlist")==True:
            self.notifier.set_skip_taskbar_hint(True) #hide from the window list applet

        if saved_window_width != None and saved_window_height != None:#check if the size is not 0
            self.wTree.get_widget("notifier").resize(saved_window_width, saved_window_height)
            self.specto.logger.log(_("notifier: size set"), "debug", self.__class__)
        else:
            self.specto.logger.log(_("notifier: size not set"), "debug", self.__class__)
            
        if saved_window_x != None and saved_window_y != None:#check if the position is not 0
            self.wTree.get_widget("notifier").move(saved_window_x, saved_window_y)
            self.specto.logger.log(_("notifier: position set"), "debug", self.__class__)
        else:
            self.specto.logger.log(_("notifier: position not set"), "debug", self.__class__)

    def save_size_and_position(self):
        """
        Save the size and position from the notifier in gconf when the window is closed.
        """
        #save the size in gconf
        current_window_size = self.wTree.get_widget("notifier").get_size()
        current_window_width = current_window_size[0]
        current_window_height = current_window_size[1]
        #save in gconf
        self.specto.specto_gconf.set_entry("window_notifier_width", current_window_width)
        self.specto.specto_gconf.set_entry("window_notifier_height", current_window_height)

        #save the window position in gconf when the window is closed
        current_window_xy = self.wTree.get_widget("notifier").get_position()
        current_window_x = current_window_xy[0]
        current_window_y = current_window_xy[1]
        #save in gconf
        self.specto.specto_gconf.set_entry("window_notifier_x", current_window_x)
        self.specto.specto_gconf.set_entry("window_notifier_y", current_window_y)

    def get_state(self):
        """ Return True if the notifier window is visible. """
        if self.notifier.flags()  & gtk.VISIBLE:
            return True
        else:
            return False
        
    def create_notifier_gui(self):
        """ Create the gui from the notifier. """
        self.treeview=self.wTree.get_widget("treeview")
        self.treeview.set_model(self.model)
        self.treeview.set_flags(gtk.TREE_MODEL_ITERS_PERSIST)
        self.wTree.get_widget("button_clear_all").set_sensitive(False)
        self.wTree.get_widget("clear_all1").set_sensitive(False)


        ### Initiate the window
        self.restore_size_and_position()
        self.show_toolbar = self.specto.specto_gconf.get_entry("show_toolbar")
        if  self.show_toolbar == False:
            self.wTree.get_widget("display_toolbar").set_active(False)
            self.toggle_display_toolbar()
        else:
            self.wTree.get_widget("display_toolbar").set_active(True)
            self.toggle_display_toolbar()
            
        if self.specto.specto_gconf.get_entry("show_deactivated_watches") == True:
            self.wTree.get_widget("display_all_watches").set_active(True)
        else:
            self.wTree.get_widget("display_all_watches").set_active(False)
    
        if self.specto.specto_gconf.get_entry("show_notifier") == True:
            self.notifier.show()

        ### Checkbox
        self.columnCheck_renderer = gtk.CellRendererToggle()
        self.columnCheck_renderer.set_property("activatable", True)
        self.columnCheck_renderer.connect("toggled", self.check_clicked, self.model)
        self.columnCheck = gtk.TreeViewColumn(_("Active"), self.columnCheck_renderer, active=0)
        self.columnCheck.connect("clicked", self.sort_column_active)
        self.columnCheck.set_sort_column_id(0)
        self.treeview.append_column(self.columnCheck)

        ### Icon
        self.columnIcon_renderer = gtk.CellRendererPixbuf()
        self.columnIcon = gtk.TreeViewColumn(_("Type"), self.columnIcon_renderer, pixbuf=1)
        self.columnIcon.set_clickable(True)
        self.columnIcon.connect("clicked", self.sort_column_type)
        self.treeview.append_column(self.columnIcon)

        ### Titre
        self.columnTitle_renderer = gtk.CellRendererText()
        self.columnTitle_renderer.set_property("editable", True)
        self.columnTitle_renderer.connect('edited', self.change_entry_name)
        self.columnTitle = gtk.TreeViewColumn(_("Name"), self.columnTitle_renderer, text=2, weight=5)
        self.columnTitle.connect("clicked", self.sort_column_name)
        self.columnTitle.set_expand(True)
        self.columnTitle.set_resizable(True)
        self.columnTitle.set_sort_column_id(2)
        self.treeview.append_column(self.columnTitle)
        
        ### ID
        self.columnID_renderer = gtk.CellRendererText()
        self.columnID = gtk.TreeViewColumn(_("ID"), self.columnID_renderer, markup=3)
        self.columnID.set_visible(False)
        self.columnID.set_sort_column_id(3)
        self.treeview.append_column(self.columnID)
        
        ### type
        self.renderer = gtk.CellRendererText()
        self.columnType = gtk.TreeViewColumn(_("TYPE"), self.renderer, markup=4)
        self.columnType.set_visible(False)
        self.columnType.set_sort_column_id(4)
        self.treeview.append_column(self.columnType)
        
        self.get_startup_sort_order()
            

        ###Create info-panel
        vbox_info = self.wTree.get_widget("vbox_info")

        #show tip of the day
        self.quicktip = self.get_quick_tip()
        self.lblTip = gtk.Label(("<big>" + _("Tip of the Day:") + "</big> "+ self.quicktip))
        self.lblTip.set_line_wrap(True)
        self.lblTip.set_use_markup(True)
        self.lblTip.show()
        vbox_info.pack_start(self.lblTip, False, False, 0)
        self.wTree.get_widget("imgWatch").set_from_pixbuf(self.specto.icon_theme.load_icon("dialog-information", 64, 0))

        #hide the buttons
        self.wTree.get_widget("vbox_panel_buttons").hide()
        
        self.wTree.get_widget("edit").set_sensitive(False)
        self.notebook_info = self.wTree.get_widget("notebook_info")

        
    def show_add_watch(self, widget):
        """ Call the main function to show the add watch window. """
        self.specto.show_add_watch()

    def show_edit_watch(self, widget):
        """ Call the main function to show the edit watch window. """
        model, iter = self.treeview.get_selection().get_selected()
        if model.iter_is_valid(iter):
            id = int(model.get_value(iter, 3))
            self.specto.show_edit_watch(id)

    def show_preferences(self, widget):
        """ Call the main function to show the preferences window. """
        self.specto.show_preferences()
    
    def show_error_log(self, *widget):
        """ Call the main function to show the log window. """
        self.specto.show_error_log()
        
    def show_help(self, *args):
        """ Call the main function to show the help. """
        self.specto.show_help()
        
    def show_about(self, *args):
        """ Call the main function to show the about window. """
        self.specto.show_about()
        
        
### Sort functions ###

    def get_startup_sort_order(self):
        order = self.get_gconf_sort_order()
        sort_function = self.specto.specto_gconf.get_entry("sort_function")
        if  sort_function == "name":
            self.wTree.get_widget("by_name").set_active(True)
            self.model.set_sort_column_id(2, order)
        elif sort_function == "type":
            self.wTree.get_widget("by_watch_type").set_active(True)
            self.model.set_sort_column_id(4, order)
        elif sort_function == "active":
            self.wTree.get_widget("by_watch_active").set_active(True)
            self.model.set_sort_column_id(0, order)
            
    def get_gconf_sort_order(self):
        """ Get the order (asc, desc) from a gconf key. """
        order = self.specto.specto_gconf.get_entry("sort_order")
        if order == "asc":
            sort_order = gtk.SORT_ASCENDING
        else:
            sort_order = gtk.SORT_DESCENDING
            
        return sort_order
    
    def set_gconf_sort_order(self, order):
        """ Set the order (asc, desc) for a gconf keys. """
        if order == gtk.SORT_ASCENDING:
            sort_order = "asc"
        else:
            sort_order = "desc"
            
        return sort_order
        
    def sort_column_name(self, *widget):
        """ Call the sort_name function and set the sort_name menu item to active. """
        self.wTree.get_widget("by_name").set_active(True)
        self.specto.specto_gconf.set_entry("sort_order", self.set_gconf_sort_order(not self.columnTitle.get_sort_order()))
        
    def sort_name(self, *args):
        """ Sort by watch name. """
        self.model.set_sort_column_id(2, not self.columnTitle.get_sort_order())
        self.specto.specto_gconf.set_entry("sort_function", "name")
        
    def sort_column_type(self, *widget):
        """ Call the sort_type function and set the sort_type menu item to active. """
        self.wTree.get_widget("by_watch_type").set_active(True)
        self.sort_type()
        
    def sort_type(self, *args):
        """ Sort by watch type. """
        self.model.set_sort_column_id(4, not self.columnType.get_sort_order())
        self.specto.specto_gconf.set_entry("sort_function", "type")
        self.specto.specto_gconf.set_entry("sort_order", self.set_gconf_sort_order(self.columnType.get_sort_order()))
    
    def sort_column_active(self, *widget):
        """ Call the sort_active function and set the sort_active menu item to active. """
        self.wTree.get_widget("by_watch_active").set_active(True)
        self.specto.specto_gconf.set_entry("sort_order", self.set_gconf_sort_order(not self.columnCheck.get_sort_order()))
        
    def sort_active(self, *args):
        """ Sort by active watches. """
        self.model.set_sort_column_id(0, not self.columnCheck.get_sort_order())
        self.specto.specto_gconf.set_entry("sort_function", "active")



if __name__ == "__main__":
    #run the gui
    app=Notifier()
    gtk.main()
